"""
ThinkAloud.ai — Seed Script
Populates the database with sample coding problems.
Run: uv run python -m app.scripts.seed
"""
import asyncio
import sys
import os

# Add parent dir to path so app imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.db import SessionLocal
from app.models import Problem



PROBLEMS = [
    {
        "title": "Two Sum",
        "slug": "two-sum",
        "description": "Given an array of integers `nums` and an integer `target`, return the indices of the two numbers that add up to `target`.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.\n\nReturn the answer in any order.",
        "difficulty": "easy",
        "category": "arrays",
        "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9\nOnly one valid answer exists.",
        "tags": ["arrays", "hash_map"],
        "hints": [
            "A brute force approach would check every pair — O(n²).",
            "Can you use a hash map to find the complement in O(1)?",
        ],
        "starter_code": {
            "python": "def two_sum(nums: list[int], target: int) -> list[int]:\n    pass",
            "javascript": "function twoSum(nums, target) {\n    \n}",
        },
        "test_cases": [
            {"input": "nums = [2,7,11,15], target = 9", "expected_output": "[0, 1]", "is_hidden": False},
            {"input": "nums = [3,2,4], target = 6", "expected_output": "[1, 2]", "is_hidden": False},
            {"input": "nums = [3,3], target = 6", "expected_output": "[0, 1]", "is_hidden": True},
        ],
        "solution": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i",
        "is_published": True,
    },
    {
        "title": "Valid Parentheses",
        "slug": "valid-parentheses",
        "description": "Given a string `s` containing just the characters `(`, `)`, `{`, `}`, `[` and `]`, determine if the input string is valid.\n\nA string is valid if:\n1. Open brackets are closed by the same type.\n2. Open brackets are closed in the correct order.\n3. Every close bracket has a corresponding open bracket.",
        "difficulty": "easy",
        "category": "stack_queue",
        "constraints": "1 <= s.length <= 10^4\ns consists of parentheses only.",
        "tags": ["stack", "string"],
        "hints": [
            "Use a stack to track opening brackets.",
            "When you see a closing bracket, check if it matches the top of the stack.",
        ],
        "starter_code": {
            "python": "def is_valid(s: str) -> bool:\n    pass",
            "javascript": "function isValid(s) {\n    \n}",
        },
        "test_cases": [
            {"input": "s = '()'", "expected_output": "True", "is_hidden": False},
            {"input": "s = '()[]{}'", "expected_output": "True", "is_hidden": False},
            {"input": "s = '(]'", "expected_output": "False", "is_hidden": False},
            {"input": "s = '([)]'", "expected_output": "False", "is_hidden": True},
        ],
        "solution": "def is_valid(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            if not stack or stack[-1] != mapping[char]:\n                return False\n            stack.pop()\n        else:\n            stack.append(char)\n    return len(stack) == 0",
        "is_published": True,
    },
    {
        "title": "Reverse Linked List",
        "slug": "reverse-linked-list",
        "description": "Given the head of a singly linked list, reverse the list, and return the reversed list.",
        "difficulty": "easy",
        "category": "linked_lists",
        "constraints": "The number of nodes is in range [0, 5000].\n-5000 <= Node.val <= 5000",
        "tags": ["linked_list", "recursion"],
        "hints": [
            "Use three pointers: prev, current, next.",
            "At each step, reverse the current node's pointer.",
        ],
        "starter_code": {
            "python": "def reverse_list(head):\n    pass",
            "javascript": "function reverseList(head) {\n    \n}",
        },
        "test_cases": [
            {"input": "head = [1,2,3,4,5]", "expected_output": "[5,4,3,2,1]", "is_hidden": False},
            {"input": "head = [1,2]", "expected_output": "[2,1]", "is_hidden": False},
            {"input": "head = []", "expected_output": "[]", "is_hidden": True},
        ],
        "solution": "def reverse_list(head):\n    prev = None\n    current = head\n    while current:\n        next_node = current.next\n        current.next = prev\n        prev = current\n        current = next_node\n    return prev",
        "is_published": True,
    },
    {
        "title": "Maximum Subarray",
        "slug": "maximum-subarray",
        "description": "Given an integer array `nums`, find the subarray with the largest sum, and return its sum.",
        "difficulty": "medium",
        "category": "dynamic_programming",
        "constraints": "1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4",
        "tags": ["dynamic_programming", "arrays", "kadanes_algorithm"],
        "hints": [
            "Think about Kadane's Algorithm.",
            "At each position, decide: start a new subarray or extend the current one?",
        ],
        "starter_code": {
            "python": "def max_sub_array(nums: list[int]) -> int:\n    pass",
            "javascript": "function maxSubArray(nums) {\n    \n}",
        },
        "test_cases": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6", "is_hidden": False},
            {"input": "nums = [1]", "expected_output": "1", "is_hidden": False},
            {"input": "nums = [5,4,-1,7,8]", "expected_output": "23", "is_hidden": True},
        ],
        "solution": "def max_sub_array(nums):\n    max_sum = current_sum = nums[0]\n    for num in nums[1:]:\n        current_sum = max(num, current_sum + num)\n        max_sum = max(max_sum, current_sum)\n    return max_sum",
        "is_published": True,
    },
    {
        "title": "Binary Tree Level Order Traversal",
        "slug": "binary-tree-level-order",
        "description": "Given the root of a binary tree, return the level order traversal of its nodes' values (i.e., from left to right, level by level).",
        "difficulty": "medium",
        "category": "trees",
        "constraints": "The number of nodes is in range [0, 2000].\n-1000 <= Node.val <= 1000",
        "tags": ["trees", "bfs", "queue"],
        "hints": [
            "Use BFS with a queue.",
            "Process all nodes at the current level before moving to the next.",
        ],
        "starter_code": {
            "python": "def level_order(root) -> list[list[int]]:\n    pass",
            "javascript": "function levelOrder(root) {\n    \n}",
        },
        "test_cases": [
            {"input": "root = [3,9,20,null,null,15,7]", "expected_output": "[[3],[9,20],[15,7]]", "is_hidden": False},
            {"input": "root = [1]", "expected_output": "[[1]]", "is_hidden": False},
            {"input": "root = []", "expected_output": "[]", "is_hidden": True},
        ],
        "solution": "from collections import deque\ndef level_order(root):\n    if not root: return []\n    result, queue = [], deque([root])\n    while queue:\n        level = []\n        for _ in range(len(queue)):\n            node = queue.popleft()\n            level.append(node.val)\n            if node.left: queue.append(node.left)\n            if node.right: queue.append(node.right)\n        result.append(level)\n    return result",
        "is_published": True,
    },
    {
        "title": "Longest Substring Without Repeating Characters",
        "slug": "longest-substring-no-repeat",
        "description": "Given a string `s`, find the length of the longest substring without repeating characters.",
        "difficulty": "medium",
        "category": "strings",
        "constraints": "0 <= s.length <= 5 * 10^4\ns consists of English letters, digits, symbols and spaces.",
        "tags": ["strings", "sliding_window", "hash_map"],
        "hints": [
            "Use a sliding window approach.",
            "Track character positions with a hash map to efficiently shrink the window.",
        ],
        "starter_code": {
            "python": "def length_of_longest_substring(s: str) -> int:\n    pass",
            "javascript": "function lengthOfLongestSubstring(s) {\n    \n}",
        },
        "test_cases": [
            {"input": "s = 'abcabcbb'", "expected_output": "3", "is_hidden": False},
            {"input": "s = 'bbbbb'", "expected_output": "1", "is_hidden": False},
            {"input": "s = 'pwwkew'", "expected_output": "3", "is_hidden": False},
            {"input": "s = ''", "expected_output": "0", "is_hidden": True},
        ],
        "solution": "def length_of_longest_substring(s):\n    char_index = {}\n    left = max_len = 0\n    for right, char in enumerate(s):\n        if char in char_index and char_index[char] >= left:\n            left = char_index[char] + 1\n        char_index[char] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len",
        "is_published": True,
    },
    {
        "title": "Number of Islands",
        "slug": "number-of-islands",
        "description": "Given an `m x n` 2D binary grid which represents a map of `1`s (land) and `0`s (water), return the number of islands.\n\nAn island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.",
        "difficulty": "medium",
        "category": "graphs",
        "constraints": "m == grid.length\nn == grid[i].length\n1 <= m, n <= 300\ngrid[i][j] is '0' or '1'.",
        "tags": ["graphs", "dfs", "bfs", "matrix"],
        "hints": [
            "Iterate through each cell. When you find a '1', trigger a DFS/BFS to mark the entire island.",
            "Mark visited cells to avoid counting them again.",
        ],
        "starter_code": {
            "python": "def num_islands(grid: list[list[str]]) -> int:\n    pass",
            "javascript": "function numIslands(grid) {\n    \n}",
        },
        "test_cases": [
            {"input": "grid = [['1','1','0','0','0'],['1','1','0','0','0'],['0','0','1','0','0'],['0','0','0','1','1']]", "expected_output": "3", "is_hidden": False},
            {"input": "grid = [['1','1','1'],['0','1','0'],['1','1','1']]", "expected_output": "1", "is_hidden": True},
        ],
        "solution": "def num_islands(grid):\n    if not grid: return 0\n    count = 0\n    for i in range(len(grid)):\n        for j in range(len(grid[0])):\n            if grid[i][j] == '1':\n                dfs(grid, i, j)\n                count += 1\n    return count\n\ndef dfs(grid, i, j):\n    if i < 0 or j < 0 or i >= len(grid) or j >= len(grid[0]) or grid[i][j] != '1': return\n    grid[i][j] = '0'\n    dfs(grid, i+1, j)\n    dfs(grid, i-1, j)\n    dfs(grid, i, j+1)\n    dfs(grid, i, j-1)",
        "is_published": True,
    },
    {
        "title": "Merge Intervals",
        "slug": "merge-intervals",
        "description": "Given an array of `intervals` where `intervals[i] = [start_i, end_i]`, merge all overlapping intervals, and return an array of the non-overlapping intervals.",
        "difficulty": "medium",
        "category": "sorting",
        "constraints": "1 <= intervals.length <= 10^4\nintervals[i].length == 2\n0 <= start_i <= end_i <= 10^4",
        "tags": ["sorting", "arrays", "intervals"],
        "hints": [
            "Sort intervals by start time first.",
            "Compare each interval with the last merged one — overlap if start <= previous end.",
        ],
        "starter_code": {
            "python": "def merge(intervals: list[list[int]]) -> list[list[int]]:\n    pass",
            "javascript": "function merge(intervals) {\n    \n}",
        },
        "test_cases": [
            {"input": "intervals = [[1,3],[2,6],[8,10],[15,18]]", "expected_output": "[[1,6],[8,10],[15,18]]", "is_hidden": False},
            {"input": "intervals = [[1,4],[4,5]]", "expected_output": "[[1,5]]", "is_hidden": False},
            {"input": "intervals = [[1,4],[0,4]]", "expected_output": "[[0,4]]", "is_hidden": True},
        ],
        "solution": "def merge(intervals):\n    intervals.sort(key=lambda x: x[0])\n    merged = [intervals[0]]\n    for start, end in intervals[1:]:\n        if start <= merged[-1][1]:\n            merged[-1][1] = max(merged[-1][1], end)\n        else:\n            merged.append([start, end])\n    return merged",
        "is_published": True,
    },
    {
        "title": "Climbing Stairs",
        "slug": "climbing-stairs",
        "description": "You are climbing a staircase. It takes `n` steps to reach the top.\n\nEach time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
        "difficulty": "easy",
        "category": "dynamic_programming",
        "constraints": "1 <= n <= 45",
        "tags": ["dynamic_programming", "math", "fibonacci"],
        "hints": [
            "The answer at step n is the sum of answers at step n-1 and n-2.",
            "This is essentially the Fibonacci sequence!",
        ],
        "starter_code": {
            "python": "def climb_stairs(n: int) -> int:\n    pass",
            "javascript": "function climbStairs(n) {\n    \n}",
        },
        "test_cases": [
            {"input": "n = 2", "expected_output": "2", "is_hidden": False},
            {"input": "n = 3", "expected_output": "3", "is_hidden": False},
            {"input": "n = 5", "expected_output": "8", "is_hidden": True},
        ],
        "solution": "def climb_stairs(n):\n    if n <= 2: return n\n    a, b = 1, 2\n    for _ in range(3, n + 1):\n        a, b = b, a + b\n    return b",
        "is_published": True,
    },
    {
        "title": "Coin Change",
        "slug": "coin-change",
        "description": "You are given an integer array `coins` representing coins of different denominations and an integer `amount` representing a total amount of money.\n\nReturn the fewest number of coins needed to make up that amount. If it cannot be made up, return -1.\n\nYou may assume you have an infinite number of each coin.",
        "difficulty": "hard",
        "category": "dynamic_programming",
        "constraints": "1 <= coins.length <= 12\n1 <= coins[i] <= 2^31 - 1\n0 <= amount <= 10^4",
        "tags": ["dynamic_programming", "bfs"],
        "hints": [
            "Use bottom-up DP. dp[i] = minimum coins to make amount i.",
            "For each amount, try every coin and take the minimum.",
        ],
        "starter_code": {
            "python": "def coin_change(coins: list[int], amount: int) -> int:\n    pass",
            "javascript": "function coinChange(coins, amount) {\n    \n}",
        },
        "test_cases": [
            {"input": "coins = [1,5,10], amount = 12", "expected_output": "3", "is_hidden": False},
            {"input": "coins = [2], amount = 3", "expected_output": "-1", "is_hidden": False},
            {"input": "coins = [1], amount = 0", "expected_output": "0", "is_hidden": True},
        ],
        "solution": "def coin_change(coins, amount):\n    dp = [float('inf')] * (amount + 1)\n    dp[0] = 0\n    for i in range(1, amount + 1):\n        for coin in coins:\n            if coin <= i:\n                dp[i] = min(dp[i], dp[i - coin] + 1)\n    return dp[amount] if dp[amount] != float('inf') else -1",
        "is_published": True,
    },
]


async def seed():
    async with SessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(Problem))
        count = result.scalar()
        if count > 0:
            print(f"⚠️  Database already has {count} problems. Skipping seed.")
            return

        for data in PROBLEMS:
            problem = Problem(**data)
            db.add(problem)

        await db.commit()
        print(f"✅ Seeded {len(PROBLEMS)} problems successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
