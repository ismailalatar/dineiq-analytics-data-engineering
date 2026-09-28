"""DineIQ professional dark theme."""

CSS = """
<style>
    .stApp { background: linear-gradient(135deg, #0E1117 0%, #131820 100%); }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #131820 0%, #0E1117 100%);
        border-right: 1px solid #2D3548;
    }

    .metric-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 1px solid #2D3548;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #FF6B35;
        box-shadow: 0 4px 20px rgba(255,107,53,0.15);
        transform: translateY(-2px);
    }
    .metric-label { color: #A0A8B8; font-size: 13px; text-transform: uppercase;
                    letter-spacing: 0.5px; margin-bottom: 8px; }
    .metric-value { color: #FFFFFF; font-size: 32px; font-weight: 700; margin: 0;
                    line-height: 1.2; }

    .page-title { color: #FFFFFF; font-size: 32px; font-weight: 700; margin-bottom: 4px; }
    .page-subtitle { color: #6B7280; font-size: 14px; margin-bottom: 24px; }

    .section-header {
        color: #FFFFFF; font-size: 18px; font-weight: 600;
        margin: 24px 0 12px 0; padding-bottom: 8px;
        border-bottom: 2px solid #FF6B35; display: inline-block;
    }

    .empty-state {
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 2px dashed #2D3548;
        border-radius: 12px; padding: 48px 24px;
        text-align: center; margin: 24px 0;
    }
    .empty-icon { font-size: 64px; margin-bottom: 16px; }
    .empty-title { color: #FFFFFF; font-size: 20px; font-weight: 600; margin-bottom: 8px; }
    .empty-desc { color: #A0A8B8; font-size: 14px; }

    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px;
             font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .badge-critical { background: rgba(255,71,87,0.2); color: #FF4757; border: 1px solid #FF4757; }
    .badge-high { background: rgba(255,184,0,0.2); color: #FFB800; border: 1px solid #FFB800; }
    .badge-medium { background: rgba(74,158,255,0.2); color: #4A9EFF; border: 1px solid #4A9EFF; }
    .badge-low { background: rgba(160,168,184,0.2); color: #A0A8B8; border: 1px solid #A0A8B8; }
    .badge-success { background: rgba(0,200,150,0.2); color: #00C896; border: 1px solid #00C896; }

    .user-avatar {
        width: 48px; height: 48px; border-radius: 50%;
        background: linear-gradient(135deg, #FF6B35, #FF8555);
        color: white; display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 20px; margin-bottom: 12px;
    }

    .info-banner {
        background: linear-gradient(135deg, rgba(74,158,255,0.1), rgba(74,158,255,0.05));
        border: 1px solid rgba(74,158,255,0.3);
        border-radius: 8px; padding: 16px 20px; margin: 16px 0; color: #FFFFFF;
    }

    .login-container {
        max-width: 480px; margin: 5% auto;
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 1px solid #2D3548; border-radius: 16px;
        padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .login-logo { font-size: 64px; text-align: center; margin-bottom: 8px; }
    .login-title { color: #FFFFFF; font-size: 28px; font-weight: 700;
                   text-align: center; margin-bottom: 4px; }
    .login-subtitle { color: #A0A8B8; font-size: 14px;
                      text-align: center; margin-bottom: 24px; }

    .stButton > button {
        background: linear-gradient(135deg, #FF6B35, #FF8555);
        color: white; border: none; border-radius: 8px; font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 15px rgba(255,107,53,0.4);
        transform: translateY(-1px);
    }

    .stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #2D3548; }

    .rec-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #212838 100%);
        border: 1px solid #2D3548; border-left: 4px solid #FF6B35;
        border-radius: 8px; padding: 16px 20px; margin: 12px 0;
    }
    .rec-action {
        background: rgba(0,200,150,0.08); border-left: 3px solid #00C896;
        padding: 10px 14px; border-radius: 4px; margin-top: 10px;
        color: #D0D8E8; font-size: 14px;
    }
</style>
"""

COLORS = {
    "orange": "#FF6B35",
    "blue": "#4A9EFF",
    "green": "#00C896",
    "yellow": "#FFB800",
    "red": "#FF4757",
    "gray": "#A0A8B8",
}
