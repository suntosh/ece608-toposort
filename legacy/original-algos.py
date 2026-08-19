import networkx
import sys

def dfs(depth) -> int:
    """Echo the input arguments to standard output"""
    print("This is DFS %s" % (depth))
    return 0

def bfs(depth) -> int:
    """Echo the input arguments to standard output"""
    print("This is BFS %s" % (depth))
    return 0

if __name__ == '__main__':
    dfs(100)
    bfs(100)


