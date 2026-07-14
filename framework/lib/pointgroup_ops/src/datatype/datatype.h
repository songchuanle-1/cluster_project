#ifndef DATATYPE_H
#define DATATYPE_H
#include <cstdint>
#include <array>
#include <vector>
#include <queue>
#include <limits>

// 优先使用 google dense_hash_map, 如果系统未安装 sparsehash 则回退到 std::unordered_map
#ifdef USE_DENSE_HASH
#include <google/dense_hash_map>
#else
#include <unordered_map>
#endif

using Int = int32_t;

template <Int dimension> using Point = std::array<Int, dimension>;

template <Int dimension> struct IntArrayHash{
    std::size_t operator()(Point<dimension> const &p) const{
        Int hash = 16777619;
        for(auto x : p){
            hash *= 2166136261;
            hash ^= x;
        }
        return hash;
    }
};

template <Int dimension>
#ifdef USE_DENSE_HASH
using SparseGridMap = google::dense_hash_map<Point<dimension>, Int, IntArrayHash<dimension>, std::equal_to<Point<dimension>>>; // <Key, Data, HashFcn, EqualKey, Alloc>
#else
using SparseGridMap = std::unordered_map<Point<dimension>, Int, IntArrayHash<dimension>, std::equal_to<Point<dimension>>>; // fallback implementation
#endif

template <Int dimension> class SparseGrid{
public:
    Int ctr;
    SparseGridMap<dimension> mp;
    SparseGrid();
};

template <Int dimension> using SparseGrids = std::vector<SparseGrid<dimension>>;

using RuleBook = std::vector<std::vector<Int>>;

class ConnectedComponent{
public:
    std::vector<Int> pt_idxs;

    ConnectedComponent();
    void addPoint(Int pt_idx);
};

using ConnectedComponents = std::vector<ConnectedComponent>;

#endif //DATATYPE_H
