class Solution:
    def dailyTemperatures(self, temperatures):
        n = len(temperatures)
        dp = [0]*n

        for i in range(n-2,-1,-1):
            if temperatures[i] < temperatures[i+1]:
                dp[i] = 1
            else:
                ## 递归
                begin = i + 1
                flag = False
                while dp[begin] !=0:
                    print(begin)
                    print(temperatures[i],temperatures[begin])
                    begin = begin + dp[begin]
                    if temperatures[begin] > temperatures[i]:
                        flag = True
                        break
                        

                if flag: 
                    dp[i] = begin - i
                else: dp[i] = 0
        
        return dp


ss = Solution()
temperatures = [73,74,75,71,69,72,76,73]
print(ss.dailyTemperatures(temperatures))