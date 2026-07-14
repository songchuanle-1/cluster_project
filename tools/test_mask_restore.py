import torch
from framework.model.mamba_model.model_base2_mamba.quard import indices_from_mask, restore_to_original_order


def main():
    M = 10
    x = torch.arange(M)
    # 假设聚类掩码（选取偶数索引）
    mask = (x % 2 == 0)
    idx = indices_from_mask(mask)
    # 在子集上做一些计算，例如值为原索引乘以 10
    values = (idx * 10).to(torch.long)
    restored = restore_to_original_order(M, idx, values)
    print('mask:', mask)
    print('indices:', idx)
    print('values:', values)
    print('restored:', restored)


if __name__ == '__main__':
    main()
