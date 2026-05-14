# test.py
# 简单测试：调用 Agent，让它回答问题或执行任务

from agent import invoke_agent

user_input = "根据公司的考勤制度，迟到两次会怎么处理？"

print("用户提问：", user_input)
print("Agent 回复：")
response = invoke_agent(user_input, thread_id="test1")
print(response)