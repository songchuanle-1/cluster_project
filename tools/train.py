import argparse
import datetime
import gorilla
import os
import os.path as osp
import shutil
import time
import torch
import numpy as np
from tensorboardX import SummaryWriter
from tqdm import tqdm

from framework.dataset import build_dataloader, build_dataset
from framework import resolve_network
from framework.utils import AverageMeter, get_root_logger
import copy
import torch.multiprocessing as mp
mp.set_sharing_strategy('file_system')  # 使用文件系统替代共享内存
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# PyTorch 2.6+ defaults weights_only=True.  This project loads trusted local
# checkpoints and preprocessed ScanNet .pth files that contain numpy objects,
# so use the legacy full-pickle loader unless a caller explicitly overrides it.
# Older PyTorch versions do not accept the weights_only keyword; retry without
# it only when that compatibility error is raised.
_original_torch_load = torch.load
def _torch_load_compat(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    try:
        return _original_torch_load(*args, **kwargs)
    except TypeError as exc:
        if 'weights_only' not in str(exc):
            raise
        kwargs.pop('weights_only', None)
        return _original_torch_load(*args, **kwargs)
torch.load = _torch_load_compat 

def _print_results_acc(iou_25, iou_50, logger):
    logger.info(f"{'=' * 100}")
    logger.info("{0:<12}{1:<12}{2:<12}{3:<12}{4:<12}{5:<12}{6:<12}"
               .format("IoU", "zt_w_d", "zt_wo_d", "st_w_d", "st_wo_d", "mt", "overall"))
    logger.info(f"{'-' * 100}")
    line_1_str = '{:<12}'.format("0.25")
    for sub_group_type, score in iou_25.items():
        line_1_str += '{:<12.1f}'.format(score * 100)
    logger.info(line_1_str)
    line_2_str = '{:<12}'.format("0.50")
    for sub_group_type, score in iou_50.items():
        line_2_str += '{:<12.1f}'.format(score * 100)
    logger.info(line_2_str)
    logger.info(f"{'=' * 100}")

    print(f"{'=' * 100}")
    print("{0:<12}{1:<12}{2:<12}{3:<12}{4:<12}{5:<12}{6:<12}"
               .format("IoU", "zt_w_d", "zt_wo_d", "st_w_d", "st_wo_d", "mt", "overall"))
    print(f"{'-' * 100}")
    line_1_str = '{:<12}'.format("0.25")
    for sub_group_type, score in iou_25.items():
        line_1_str += '{:<12.1f}'.format(score * 100)
    print(line_1_str)
    line_2_str = '{:<12}'.format("0.50")
    for sub_group_type, score in iou_50.items():
        line_2_str += '{:<12.1f}'.format(score * 100)
    print(line_2_str)
    print(f"{'=' * 100}")
def get_args():
    parser = argparse.ArgumentParser('SPFormer')
    parser.add_argument('config', type=str, help='path to config file')
    parser.add_argument('--resume', type=str, help='path to resume from')
    # parser.add_argument('--work_dir', type=str, help='working directory')

    parser.add_argument('--save_ckpt', type=bool,default=True, help='skip validation')
    parser.add_argument('--skip_validate', action='store_true', help='skip validation')
    parser.add_argument('--skip_training', action='store_true', help='skip training')
    # parser.add_argument('--skip_training', type=bool, default=True, help='skip training')
    parser.add_argument('--dist', action='store_true', help='if distributed')
    parser.add_argument('--num_gpus', type=int, default=1, help='number of gpus')
    parser.add_argument('--num_machines', type=int, default=1, help='number of machines')
    parser.add_argument('--machine_rank', type=int, default=0, help='rank of machine')
    parser.add_argument('--dist_url', type=str, default="auto", help='distributed training url')
    parser.add_argument('--gpu_ids', type=int, default=[0, 1], nargs='+', help='ids of gpus to use')

    args = parser.parse_args()
    return args

def list_avg(x):
    return sum(x) / len(x)
def dict_val(metric_dict):
    out = {}
    for k, v in metric_dict.items():
        out[k] = v.val
    return out

def train(epoch, model, dataloader, optimizer, lr_scheduler, cfg, logger, writer):
    model.train()
    iter_time = AverageMeter()
    data_time = AverageMeter()
    meter_dict = {}
    end = time.time()

    if dataloader.sampler is not None and cfg.dist:
        dataloader.sampler.set_epoch(epoch)
    progress_bar = tqdm(total=len(dataloader), desc=f'Train[{epoch}/{cfg.train.epochs}]',bar_format="{l_bar}{bar:20}{r_bar}")
    for i, batch in enumerate(dataloader, start=1):
        data_time.update(time.time() - end)
        # forward
        # torch.autograd.set_detect_anomaly(True)
        loss, log_vars = model(batch, mode='loss')
        # reduce log_vars for multi-gpu
        # print(log_vars)
        log_vars = gorilla.reduce_dict(log_vars, average=True)
        if gorilla.is_main_process():
            # meter_dict
            for k, v in log_vars.items():
                if k not in meter_dict.keys():
                    meter_dict[k] = AverageMeter()
                meter_dict[k].update(v.item())


        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logger.info("Skipping backward due to unstable loss")
            optimizer.zero_grad()  # 清除梯度
            continue   # 跳过该批次
        else:
            optimizer.zero_grad()
            loss.backward()
            if cfg.train.grad_clip > 0:
                grad_total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.train.grad_clip)
            optimizer.step()
        # backward
        # optimizer.zero_grad()
        # loss.backward()
        # #with torch.autograd.detect_anomaly():
        # #     loss.backward()
        
        # # clip grad
        # if cfg.train.grad_clip > 0:
        #     grad_total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.train.grad_clip)
            
        # optimizer.step()

        # time and print
        remain_iter = len(dataloader) * (cfg.train.epochs - epoch + 1) - i
        iter_time.update(time.time() - end)
        end = time.time()
        remain_time = remain_iter * iter_time.avg
        remain_time = str(datetime.timedelta(seconds=int(remain_time)))
        lr = optimizer.param_groups[0]['lr']
        
        if i % 10 == 0 and gorilla.is_main_process():
            log_str = f'Epoch [{epoch}/{cfg.train.epochs}][{i}/{len(dataloader)}]  '
            log_str += f'lr: {lr:.2g}, eta: {remain_time}, '
            log_str += f'data_time: {data_time.avg:.2f}, iter_time: {iter_time.avg:.2f}'
            
            meter_dict_print = meter_dict
            for k, v in meter_dict_print.items():
                log_str += f', {k}: {v.val:.4f}'
                writer.add_scalar(f'train/{k}', v.val, i+(epoch-1)*len(dataloader))
            if cfg.train.grad_clip > 0:
                writer.add_scalar('train/grad_total_norm', grad_total_norm, i+(epoch-1)*len(dataloader))
                log_str += f', grad_total_norm: {grad_total_norm:.4f}'
            logger.info(log_str)
            writer.add_scalar('train/learning_rate', lr, i+(epoch-1)*len(dataloader))
        
        if gorilla.is_main_process():
            logger_dict = { 'lr':f'{lr:.2g}', 'eta': f'{remain_time}', 'iter_time': f'{iter_time.avg:.2f}'}
            logger_dict0 = { 'lr':f'{lr:.2g}', 'eta': f'{remain_time}', 'iter_time': f'{iter_time.avg:.2f}'}
            for k,v in meter_dict.items():    
                logger_dict[f"{k}"] = f"{v.val:.4f}" 

            progress_bar.set_postfix(logger_dict0)
            progress_bar.update()

    gorilla.synchronize()            
    # update lr
    lr_scheduler.step()
    lr = optimizer.param_groups[0]['lr']

    # save checkpoint
    # if gorilla.is_main_process():
    #     save_file = osp.join(cfg.work_dir, 'last.pth')
    #     meta = dict(epoch=epoch)
    #     gorilla.save_checkpoint(model, save_file, optimizer, lr_scheduler, meta)

@torch.no_grad()
def model_profile(model, cfg, logger):
    """
    训练前自动计算并记录模型指标：参数量、FLOPs、推理时间。
    使用 val 数据集的单条样本 (lang_num_max=1) 做推理。
    """
    if not gorilla.is_main_process():
        return

    logger.info("=" * 70)
    logger.info("  Model Profile (before training)")
    logger.info("=" * 70)

    # ---- 1. 参数量 ----
    count_parameters = gorilla.parameter_count(model)['']
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    frozen_params = count_parameters - trainable_params
    logger.info(f"  Total params:     {count_parameters / 1e6:.2f} M")
    logger.info(f"  Trainable params: {trainable_params / 1e6:.2f} M")
    logger.info(f"  Frozen params:    {frozen_params / 1e6:.2f} M")

    # ---- 2. 构建 profiling dataloader ----
    profile_data_cfg = copy.deepcopy(cfg.data.val)
    profile_data_cfg['lang_num_max'] = 1
    profile_dataset = build_dataset(profile_data_cfg, logger)
    profile_dl_cfg = copy.deepcopy(cfg.dataloader.val)
    profile_dl_cfg['batch_size'] = 1
    profile_dataloader = build_dataloader(profile_dataset, training=False, **profile_dl_cfg)

    device = next(model.parameters()).device
    model.eval()
    sample_batch = next(iter(profile_dataloader))

    # ---- 3. FLOPs (可选, 需要 fvcore) ----
    try:
        from fvcore.nn import FlopCountAnalysis
        flops_analysis = FlopCountAnalysis(model, (sample_batch, 'predict'))
        flops = flops_analysis.total()
        logger.info(f"  FLOPs:            {flops / 1e9:.2f} G  ({flops:.0f})")
    except ImportError:
        logger.info("  FLOPs:            skipped (fvcore not installed, pip install fvcore)")

    # ---- 4. 推理时间 (forward only, 单条样本) ----
    n_warmup = 3
    n_iter  = 10
    # warmup
    for _ in range(n_warmup):
        _ = model(sample_batch, mode='predict')
    torch.cuda.synchronize(device)

    # timing
    times = []
    for _ in range(n_iter):
        torch.cuda.synchronize(device)
        t0 = time.perf_counter()
        _ = model(sample_batch, mode='predict')
        torch.cuda.synchronize(device)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    times_arr = np.array(times)
    mean_t   = times_arr.mean() * 1000.0   # ms
    median_t = np.median(times_arr) * 1000.0
    std_t    = times_arr.std() * 1000.0
    logger.info(f"  Inference time:   {mean_t:.1f} ± {std_t:.1f} ms  (median {median_t:.1f} ms, n={n_iter})")
    logger.info(f"  Throughput:       {1000.0 / mean_t:.1f} samples/s")
    logger.info("=" * 70)

    del profile_dataloader   

@torch.no_grad()
def eval(epoch, best_iou, model, dataloader, cfg, logger, writer, save_ckp=False):
    if gorilla.is_main_process():
        logger.info('Validation')
        pious, spious, sp_r_ious, p_r_ious, nt_labels, meta_datas, view_dependents, scan_ids = [], [], [], [], [], [], [], []
        progress_bar = tqdm(total=len(dataloader), desc=f'Val[{epoch}/{cfg.train.epochs}]', bar_format="{l_bar}{bar:20}{r_bar}" )

    model.eval()
    for batch in dataloader:
        result = model(batch, mode='predict')
        piou = result['piou']
        spiou = result['spiou']
        nt_label = result['nt_label']
        scan_id = result['scan_id']
        if gorilla.is_main_process():
            pious.extend(piou)
            spious.extend(spiou)
            nt_labels.extend(nt_label)
            scan_ids.extend(scan_id)
            if 'sp_r_iou' in result.keys():
                sp_r_ious.extend(result['sp_r_iou'])
                p_r_ious.extend(result['p_r_iou'])
            if 'meta_datas' in result.keys():
                meta_datas.extend(result['meta_datas'])
                #view_dependents.extend(result['view_dependents'])
            else:
                # Keep alignment with scan_ids to avoid index mismatch.
                meta_datas.extend([None] * len(scan_id))
            progress_bar.update()
    
    # evaluate
    miou = None
    if gorilla.is_main_process():
        progress_bar.close()
        logger.info('Evaluate referring segmentation: '+str(len(pious)))
        has_valid_meta = (
            len(meta_datas) == len(scan_ids)
            and len(meta_datas) > 0
            and all(
                (m is not None) and isinstance(m, dict) and ('eval_type' in m)
                for m in meta_datas
            )
        )

        acc_half_results = None
        acc_quarter_results = None

        if len(nt_labels) > 0 and has_valid_meta:
            eval_dict = {"zt_w_d": 0, "zt_wo_d": 1, "st_w_d": 2, "st_wo_d": 3, "mt": 4}
            eval_type_mask = np.empty(len(scan_ids))
            for idx, scan_id in enumerate(scan_ids):
                eval_type = meta_datas[idx].get('eval_type', 'mt')
                if eval_type not in eval_dict:
                    eval_type = 'mt'
                eval_type_mask[idx] = eval_dict[eval_type]
                if nt_labels[idx]:
                    pious[idx] = torch.tensor(0.0)
                if eval_type in ("zt_wo_d", "zt_w_d"):
                    if nt_labels[idx]:
                        pious[idx] = torch.tensor(1.0)
                        spious[idx] = torch.tensor(1.0)
                    else:
                        pious[idx] = torch.tensor(0.0)
                        spious[idx] = torch.tensor(0.0)
            pious = torch.stack(pious, dim=0).cpu().numpy()
            acc_half_results = {}
            acc_quarter_results = {}
            for sub_group in ("zt_w_d", "zt_wo_d", "st_w_d", "st_wo_d", "mt"):
                selected_indices = eval_type_mask == eval_dict[sub_group]
                selected = pious[selected_indices]      
                acc_half_results[sub_group] = (selected > 0.5).sum().astype(float) / selected.size
                acc_quarter_results[sub_group] = (selected > 0.25).sum().astype(float) / selected.size
                writer.add_scalar('val/'+ sub_group + '_25', acc_quarter_results[sub_group], epoch)
                writer.add_scalar('val/'+ sub_group + '_50', acc_half_results[sub_group], epoch)
        elif len(nt_labels) > 0 and not has_valid_meta:
            logger.warning(
                'Skip eval_type subgroup metrics due to missing/unaligned meta_datas: '
                f'len(meta_datas)={len(meta_datas)}, len(scan_ids)={len(scan_ids)}'
            )
            pious = torch.stack(pious, dim=0).cpu().numpy()
        else:        
            pious = torch.stack(pious, dim=0).cpu().numpy()
        
        precision_half = (pious > 0.5).sum().astype(float) / pious.size
        precision_quarter = (pious > 0.25).sum().astype(float) / pious.size
        miou = pious.mean()

        spious = torch.stack(spious, dim=0).cpu().numpy()
        spprecision_half = (spious > 0.5).sum().astype(float) / spious.size
        spprecision_quarter = (spious > 0.25).sum().astype(float) / spious.size
        spmiou = spious.mean()

        writer.add_scalar('val/mIOU', miou, epoch)
        writer.add_scalar('val/Acc_50', precision_half, epoch)
        writer.add_scalar('val/Acc_25', precision_quarter, epoch)
        writer.add_scalar('val/spmIOU', spmiou, epoch)
        writer.add_scalar('val/spAcc_50', spprecision_half, epoch)
        writer.add_scalar('val/spAcc_25', spprecision_quarter, epoch)
        
        logger.info(f'mIoU : {miou}')
        if len(nt_labels) > 0 and acc_half_results is not None and acc_quarter_results is not None:
            acc_half_results["overall"] = precision_half
            acc_quarter_results["overall"] = precision_quarter
            _print_results_acc(acc_quarter_results, acc_half_results, logger)
        else:
            logger.info('mIOU: {:.3f}. Acc_50: {:.3f}. Acc_25: {:.3f}'.format(miou, precision_half,
                                                                    precision_quarter))
            print('mIOU: {:.3f}. Acc_50: {:.3f}. Acc_25: {:.3f}'.format(miou, precision_half,
                                                                    precision_quarter))
        logger.info('spmIOU: {:.3f}. spAcc_50: {:.3f}. spAcc_25: {:.3f}'.format(spmiou, spprecision_half,
                                                                      spprecision_quarter))
        print('spmIOU: {:.3f}. spAcc_50: {:.3f}. spAcc_25: {:.3f}'.format(spmiou, spprecision_half,
                                                                      spprecision_quarter))        
        if len(sp_r_ious) > 0:
            sp_r_ious = torch.stack(sp_r_ious, dim=0).cpu().numpy()
            p_r_ious = torch.stack(p_r_ious, dim=0).cpu().numpy()
            sp_rmiou = sp_r_ious.mean()
            p_rmiou = p_r_ious.mean()
            writer.add_scalar('val/sp_r_mIOU', sp_rmiou, epoch)
            writer.add_scalar('val/p_r_mIOU', p_rmiou, epoch)
            logger.info('sp_r_mIOU: {:.3f}'.format(sp_rmiou))
            logger.info('p_r_mIOU: {:.3f}'.format(p_rmiou))
            print('sp_r_mIOU: {:.3f}'.format(sp_rmiou))
            print('p_r_mIOU: {:.3f}'.format(p_rmiou))


    # if gorilla.is_main_process() and save_ckp:
    #     # save
    #     if miou > best_iou:
    #         save_file = osp.join(cfg.work_dir, f'best.pth')
    #         gorilla.save_checkpoint(model, save_file)
    #     elif epoch > cfg.train.save_epoch:
    #         save_file = osp.join(cfg.work_dir, f'epoch_{epoch:04d}.pth')
    #         gorilla.save_checkpoint(model, save_file)

    return miou


def main(args):
    #os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    cfg = gorilla.Config.fromfile(args.config)
    cfg.dist = args.dist

    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    # if args.work_dir:
    if cfg.work_dir:
        cfg.work_dir = osp.join(cfg.work_dir, osp.splitext(osp.basename(args.config))[0], timestamp)
    else:
        cfg.work_dir = osp.join('./exps', osp.splitext(osp.basename(args.config))[0], timestamp)

    os.makedirs(osp.abspath(cfg.work_dir), exist_ok=True)
    log_file = osp.join(cfg.work_dir, f'{timestamp}.log')
    if gorilla.is_main_process():
        logger = get_root_logger(log_file=log_file)
        logger.info(f'config: {args.config}')
    else:
        logger = None
    shutil.copy(args.config, osp.join(cfg.work_dir, osp.basename(args.config)))
    writer = SummaryWriter(cfg.work_dir)

    # seed
    gorilla.set_random_seed(cfg.train.seed)

    # model
    model = resolve_network(args.config)(**cfg.model).cuda()
        # optimizer and scheduler
    optimizer = gorilla.build_optimizer(model, cfg.optimizer)
    lr_scheduler = gorilla.build_lr_scheduler(optimizer, cfg.lr_scheduler)

    # multi-gpu
    if args.num_gpus > 1:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[gorilla.get_local_rank()], find_unused_parameters=True)
    

    # pretrain or resume
    start_epoch = 1
    best_miou = 0.0
    miou=0.0
    if args.resume:
        # resume_path = os.path.join(cfg.work_dir,args.resume+'.pth')
        resume_path = args.resume
        if gorilla.is_main_process(): logger.info(f'Resume from {resume_path}')
        meta = gorilla.resume(model=model,
                              filename=resume_path,
                              optimizer=optimizer,
                              scheduler=lr_scheduler,
                              strict=False,
                              map_location='cpu')
        start_epoch = meta.get("epoch", 0) + 1
        best_miou = meta.get("best_miou", 0)
        logger.info(f'resume start_epoch:{start_epoch},best_miou:{best_miou}!')
        print(f'resume start_epoch:{start_epoch},best_miou:{best_miou}!')
        # print(start_epoch)
    elif cfg.train.pretrain:
        if gorilla.is_main_process(): logger.info(f'Load pretrain from {cfg.train.pretrain}')
        gorilla.load_checkpoint(model, cfg.train.pretrain, strict=False, map_location='cpu')

    cfg.dataloader.train.batch_size /= args.num_gpus
    cfg.dataloader.train.batch_size = int(cfg.dataloader.train.batch_size)
    if gorilla.is_main_process():
        logger.info(f'Train batch size per gpu: {cfg.dataloader.train.batch_size}')
    # train and val dataset
    if not args.skip_training:
        train_dataset = build_dataset(cfg.data.train, logger)
        train_loader = build_dataloader(train_dataset, dist=args.dist, **cfg.dataloader.train)
    if not args.skip_validate and gorilla.is_main_process():
        val_dataset = build_dataset(cfg.data.val, logger)
        val_loader = build_dataloader(val_dataset, **cfg.dataloader.val)

    # ─ 训练前自动 profiling: 参数量 + FLOPs + 推理时间 ─
    if not args.skip_training:
        model_profile(model, cfg, logger)

    # train and val
    if gorilla.is_main_process():
        logger.info('Training')

    for epoch in range(start_epoch, cfg.train.epochs + 1):
        # print(epoch)
        if not args.skip_training:
            train(epoch, model, train_loader, optimizer, lr_scheduler, cfg, logger, writer)
        if not args.skip_validate and (epoch % cfg.train.interval == 0) and gorilla.is_main_process():
            miou = eval(epoch, best_miou, model, val_loader, cfg, logger, writer, not args.skip_training)
            if gorilla.is_main_process(): 
                if miou > best_miou:
                    best_miou = miou
        if gorilla.is_main_process() and args.save_ckpt: 
            # meta = dict(epoch=epoch,best_miou=miou)
            meta = dict(epoch=epoch,best_miou=best_miou)
            if miou >= best_miou:
                save_file = osp.join(cfg.work_dir, f'best.pth')
                gorilla.save_checkpoint(model, save_file,optimizer, lr_scheduler,meta)
                logger.info(f'save best pth to {save_file}')
                print(f'save best pth to {save_file}')
            if epoch > cfg.train.save_epoch:
                save_file = osp.join(cfg.work_dir, f'epoch_{epoch:04d}.pth')
                gorilla.save_checkpoint(model, save_file, optimizer, lr_scheduler, meta)
                logger.info(f'save epoch pth to {save_file}') 
                print(f'save epoch pth to {save_file}') 
            save_file = osp.join(cfg.work_dir, f'last.pth')
            gorilla.save_checkpoint(model, save_file,optimizer, lr_scheduler,meta)
            logger.info(f'save last pth to {save_file}')    
            print(f'save last pth to {save_file}')    
        writer.flush()
        if args.skip_training:
            break

if __name__ == '__main__':
    args = get_args()
    if args.num_gpus > 1:
        args.dist = True
    gorilla.set_cuda_visible_devices(gpu_ids=args.gpu_ids, num_gpu=args.num_gpus)
    gorilla.launch(
        main,
        args.num_gpus,
        num_machines=args.num_machines,
        machine_rank=args.machine_rank,
        dist_url=args.dist_url,
        args=(args,) # use tuple to wrap
    )
    
