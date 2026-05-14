# webui.py
# Gradio 网页聊天界面 - 支持文件上传

import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

import shutil
import gradio as gr
from agent import invoke_agent

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 支持的文件类型
SUPPORTED_EXTS = {'.txt', '.docx', '.pptx', '.xlsx', '.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def chat(message, history, uploaded_file):
    """处理聊天消息，如果有上传文件则传给 Agent"""
    if uploaded_file is not None:
        # uploaded_file 是 Gradio 传来的临时文件路径
        file_path = uploaded_file
        # 把文件复制到我们的 uploads 目录（避免临时文件被删除）
        ext = os.path.splitext(file_path)[1].lower()
        if ext in SUPPORTED_EXTS:
            dest = os.path.join(UPLOAD_DIR, os.path.basename(file_path))
            if not os.path.exists(dest):
                shutil.copy2(file_path, dest)
            file_path = dest

        # 根据文件类型构造提示
        ext = os.path.splitext(file_path)[1].lower()
        if ext in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}:
            prompt = f"用户上传了一张图片，文件路径是：{file_path}\n\n用户说：{message}"
        else:
            prompt = f"用户上传了一个文件，文件路径是：{file_path}\n\n用户说：{message}"
    else:
        prompt = message

    reply = invoke_agent(prompt, thread_id="gradio_user")
    return reply


# ---- 构建界面 ----
with gr.Blocks(title="Cking - 影视器材专家") as demo:
    gr.Markdown("# Cking - 影视器材专家\n我是 Cking，一个专业的影视器材顾问。可以帮你分析文件、调色建议、器材推荐。")

    chatbot = gr.Chatbot(
        label="对话",
        height=400,
    )

    with gr.Row():
        msg = gr.Textbox(
            label="输入消息",
            placeholder="输入你的问题... (可以先上传文件再提问)",
            scale=4,
            show_label=False,
        )
        send_btn = gr.Button("发送", variant="primary", scale=1)

    with gr.Row():
        file_upload = gr.File(
            label="上传文件（可选）",
            file_types=[".txt", ".docx", ".pptx", ".xlsx", ".jpg", ".jpeg", ".png", ".bmp", ".webp"],
            type="filepath",
        )
        clear_btn = gr.Button("清空对话", scale=1)

    # 状态：记录上传的文件
    uploaded_state = gr.State(value=None)

    def on_file_upload(file):
        if file:
            return file, f"已上传：{os.path.basename(file)}"
        return None, "未上传文件"

    file_upload.change(
        fn=on_file_upload,
        inputs=[file_upload],
        outputs=[uploaded_state, gr.Textbox(label="文件状态", interactive=False)],
    )

    def on_send(message, history, uploaded_file):
        if not message.strip():
            return history, "", uploaded_file

        # 显示用户消息
        user_display = message
        if uploaded_file:
            user_display = f"📎 {os.path.basename(uploaded_file)}\n{message}"

        history = history + [{"role": "user", "content": user_display}]

        # 调用 Agent
        reply = chat(message, history, uploaded_file)

        history = history + [{"role": "assistant", "content": reply}]

        # 清空输入和文件状态
        return history, "", None

    send_btn.click(
        fn=on_send,
        inputs=[msg, chatbot, uploaded_state],
        outputs=[chatbot, msg, uploaded_state],
    )

    msg.submit(
        fn=on_send,
        inputs=[msg, chatbot, uploaded_state],
        outputs=[chatbot, msg, uploaded_state],
    )

    def on_clear():
        return [], "", None

    clear_btn.click(fn=on_clear, outputs=[chatbot, msg, uploaded_state])

    gr.Markdown("""
    **使用提示：**
    - 直接输入问题即可对话
    - 上传 Word/PPT/Excel 文件后，可以让 Cking 读取或修改内容
    - 上传图片后，可以让 Cking 分析拍摄参数和给出调色建议
    - 支持格式：.txt .docx .pptx .xlsx .jpg .png .bmp .webp
    """)


if __name__ == "__main__":
    auto_browser = os.environ.get("CKING_BROWSER", "1") == "1"
    print("[Cking] 启动中...", flush=True)
    demo.launch(
        inbrowser=auto_browser,
        server_name="0.0.0.0",
        server_port=7860,
    )
