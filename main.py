import os
import discord
from discord.ext import tasks
import asyncio
import time
from keep_alive import keep_alive  # Import file keep_alive của bạn

# ======================================================
# CẤU HÌNH BOT
# ======================================================

# Khởi tạo client và intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Khai báo biến toàn cục để lưu trạng thái
current_channel_id = None
current_message = "bờm thối" # Nội dung mặc định

# ======================================================
# CÁC TASK VÒNG LẶP (Loop Tasks)
# ======================================================

# 1. Task cập nhật Ping (Thay thế cho đoạn code lỗi của bạn)
@tasks.loop(seconds=15)
async def update_ping_task():
    # Tính độ trễ hiện tại
    latency = round(client.latency * 1000)
    
    # Cập nhật Status
    await client.change_presence(
        activity=discord.Activity(
            name=f"Ping: {latency}ms", 
            type=discord.ActivityType.watching
        )
    )

# 2. Task Spam tin nhắn
@tasks.loop(seconds=1) 
async def spam_task():
    global current_channel_id, current_message

    # Nếu chưa có channel ID thì không làm gì cả
    if not current_channel_id:
        return

    try:
        channel = client.get_channel(current_channel_id)
        if channel:
            await channel.send(current_message)

    except discord.errors.HTTPException as e:
        # Lỗi 429 (Too Many Requests) hoặc lỗi mạng Discord
        if e.status == 429:
            print(f"⚠️ Đang bị Discord chặn (Rate Limit). Tạm nghỉ 5 giây...")
            await asyncio.sleep(5) 
        else:
            print(f"⚠️ Lỗi HTTP: {e}")

    except Exception as e:
        print(f"❌ Lỗi không xác định trong vòng lặp: {e}")

# ======================================================
# SỰ KIỆN BOT (EVENTS)
# ======================================================

@client.event
async def on_ready():
    # Đồng bộ lệnh với Discord
    await tree.sync()
    
    # Bắt đầu vòng lặp cập nhật Ping ngay khi bot bật
    if not update_ping_task.is_running():
        update_ping_task.start()
        
    print('----------------------------------')
    print(f'🤖 Bot đã đăng nhập: {client.user}')
    print('----------------------------------')

# ======================================================
# CÁC LỆNH SLASH COMMANDS (/start, /stop)
# ======================================================

@tree.command(name="start", description="Bắt đầu Spam tin nhắn.")
@discord.app_commands.describe(
    speed="Thời gian chờ giữa mỗi tin nhắn (giây). Tối thiểu 1 giây.",
    word="Từ hoặc cụm từ mà bot sẽ gửi lặp lại."
)
async def start_command(interaction: discord.Interaction, speed: float, word: str):
    global current_channel_id, current_message

    # 1. Kiểm tra tốc độ an toàn
    if speed < 1.0: 
        await interaction.response.send_message("⚠️ Để tránh bot bị sập, tốc độ tối thiểu là **1.0 giây**.", ephemeral=True)
        return

    # 2. Kiểm tra xem bot đang chạy chưa
    if spam_task.is_running():
        await interaction.response.send_message("Bot đang chạy rồi! Hãy dùng `/stop` trước nếu muốn đổi nội dung.", ephemeral=True)
        return

    # 3. Cập nhật thông tin và chạy
    current_channel_id = interaction.channel_id
    current_message = word

    # Thay đổi tốc độ vòng lặp
    spam_task.change_interval(seconds=speed)
    spam_task.start()

    await interaction.response.send_message(f"🔥 Bắt đầu spam **'{word}'** mỗi **{speed}s** tại kênh này!", ephemeral=False)


@tree.command(name="stop", description="Dừng Spam.")
async def stop_command(interaction: discord.Interaction):
    global current_channel_id

    if spam_task.is_running():
        spam_task.stop()
        current_channel_id = None
        await interaction.response.send_message("✅ Đã dừng spam thành công.")
    else:
        await interaction.response.send_message("Bot hiện tại có chạy đâu mà dừng? 🤔", ephemeral=True)

# ======================================================
# KHỞI ĐỘNG HỆ THỐNG
# ======================================================

keep_alive()

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')

    if not TOKEN:
        print("❌ LỖI: Chưa có Token trong Secrets!")
    else:
        while True:
            try:
                client.run(TOKEN)
            except Exception as e:
                print(f"\n⚠️ Bot bị crash hoặc mất kết nối: {e}")
                print("🔄 Đang tự động khởi động lại sau 10 giây...")
                time.sleep(10)
