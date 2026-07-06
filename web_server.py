from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os

app = FastAPI()

# Cấu hình thư mục chứa giao diện HTML (Nằm cùng cấp với file này)
templates = Jinja2Templates(directory="templates")

# Khai báo cấu trúc dữ liệu nhận từ giao diện khi đăng nhập
class LoginRequest(BaseModel):
    token: str

# Hàm đọc Token từ file config.json để kiểm tra quyền truy cập Dashboard
def get_valid_token():
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
                return config.get("TOKEN", "").strip()
            except Exception:
                return ""
    return ""

# Hàm đọc dữ liệu thống kê từ file data.json của Bot
def load_bot_data():
    if os.path.exists("data.json"):
        with open("data.json", "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    # Trả về dữ liệu mặc định nếu file data.json chưa được khởi tạo hoặc bị lỗi
    return {
        "starting_balance": 0,
        "current_balance": 0,
        "internal_profit": 0,
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "commands_used": 0
    }

# =====================================================================
# INTERFACE ROUTES (Các đường dẫn trả về giao diện trang web)
# =====================================================================

# 1. Trang đăng nhập (http://127.0.0.1:8000/)
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 2. Trang Dashboard thống kê (http://127.0.0.1:8000/dashboard)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# =====================================================================
# API ENDPOINTS (Hệ thống xử lý Logic dữ liệu)
# =====================================================================

# API xử lý Đăng nhập & Lưu Token trực tiếp vào config.json
@app.post("/api/login")
async def api_login(data: LoginRequest):
    token_input = data.token.strip()
    if not token_input:
        return {"success": False, "message": "Token không được để trống!"}
        
    try:
        config_data = {}
        # Đọc dữ liệu cũ trong config.json (nếu có) để không làm mất các cài đặt khác
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                try:
                    config_data = json.load(f)
                except json.JSONDecodeError:
                    config_data = {}

        # Ghi đè/Cập nhật Token mới từ giao diện Web vào cấu hình
        config_data["TOKEN"] = token_input
        if "BET_SEQUENCE" not in config_data:
            config_data["BET_SEQUENCE"] = "Low" # Đặt mặc định nếu chưa có

        # Lưu lại vào file config.json
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            
        print("🔑 [Hệ thống] Đã cập nhật Token mới vào config.json thành công!")
        return {"success": True, "message": "Đăng nhập và lưu Token thành công!"}
        
    except Exception as e:
        print(f"❌ [Lỗi] Không thể lưu file config.json: {e}")
        return {"success": False, "message": f"Lỗi hệ thống: {str(e)}"}

# API gửi số liệu Thắng/Thua/Số dư thời gian thực cho trang Dashboard
@app.get("/api/stats")
async def api_stats(authorization: str = Header(None)):
    valid_token = get_valid_token()
    
    # Bảo mật: Nếu không có mã Authorization hoặc mã không khớp với Token trong config thì chặn lại
    if not authorization or authorization.strip() != valid_token:
        raise HTTPException(status_code=401, detail="Unauthorized - Token không hợp lệ hoặc phiên hết hạn")
    
    # Trả về toàn bộ dữ liệu đọc được từ file data.json dưới dạng JSON cho Web hiển thị
    return load_bot_data()


# Khởi chạy Web Server ở cổng 8000
if __name__ == "__main__":
    import uvicorn
    print("\n====================================================")
    print("🚀 Cat Web Dashboard đang được khởi chạy...")
    print("📱 Nếu dùng điện thoại, mở trình duyệt vào: http://127.0.0.1:8000")
    print("====================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
      
