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
# VÒNG LẶP SPAM (CORE)
# ======================================================

@bot.event
    # 3. PHẦN MỚI: Vòng lặp cập nhật Ping (Thay thế cho dòng change_presence cũ)
    # Lưu ý: Phải đặt đoạn này ở CUỐI CÙNG của hàm on_ready
    while True:
        # Tính độ trễ hiện tại
        latency = round(bot.latency * 1000) 
        
        # Cập nhật Status
        await bot.change_presence(
            activity=discord.Activity(
                name=f"Ping: {latency}ms", 
                type=discord.ActivityType.watching
            )
        )
        
        # Đợi 10 giây rồi mới cập nhật tiếp (để tránh lag bot)
        await asyncio.sleep(15)
        
@tasks.loop(seconds=1) # Mặc định là 1s, sẽ thay đổi khi dùng lệnh /start
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
            await asyncio.sleep(5) # Nghỉ 5s để Discord thả ra
        else:
            print(f"⚠️ Lỗi HTTP: {e}")

    except Exception as e:
        # Các lỗi khác (ví dụ: mất mạng, lỗi server)
        print(f"❌ Lỗi không xác định trong vòng lặp: {e}")
        # Không làm gì cả, vòng lặp sẽ tự chạy lại ở lần kế tiếp

# ======================================================
# SỰ KIỆN BOT (EVENTS)
# ======================================================

@client.event
async def on_ready():
    # Đồng bộ lệnh với Discord
    await tree.sync() 
    print('----------------------------------')
    print(f'🤖 Bot đã đăng nhập: {client.user}')
    print('----------------------------------')

# ======================================================
# CÁC LỆNH SLASH COMMANDS (/start, /stop)
# ======================================================

@tree.command(name="start", description="Bắt đầu Spam tin nhắn.")
@discord.app_commands.describe(
    speed="Thời gian chờ giữa mỗi tin nhắn (giây). Tối thiểu 1 giây để an toàn.",
    word="Từ hoặc cụm từ mà bot sẽ gửi lặp lại."
)
async def start_command(interaction: discord.Interaction, speed: float, word: str):
    global current_channel_id, current_message

    # 1. Kiểm tra tốc độ an toàn
    # Replit Free rất yếu, nên để tối thiểu 1s để tránh bị Kill
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
        current_channel_id = None # Xóa channel ID để an toàn
        await interaction.response.send_message("✅ Đã dừng spam thành công.")
    else:
        await interaction.response.send_message("Bot hiện tại có chạy đâu mà dừng? 🤔", ephemeral=True)

# ======================================================
# KHỞI ĐỘNG HỆ THỐNG (AUTO-RESTART)
# ======================================================

# 1. Bật Web Server để Uptime Robot ping
keep_alive()

# 2. Vòng lặp bất tử để chạy Bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')

    if not TOKEN:
        print("❌ LỖI: Chưa có Token trong Secrets!")
    else:
        while True:
            try:
                # Chạy bot
                client.run(TOKEN)
            except Exception as e:
                print(f"\n⚠️ Bot bị crash hoặc mất kết nối: {e}")
                print("🔄 Đang tự động khởi động lại sau 10 giây...")
                time.sleep(10)
                # Sau 10s vòng lặp while True sẽ chạy lại client.run()
