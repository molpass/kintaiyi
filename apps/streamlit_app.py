import os
import sys

# Resolve the repository root (one level up from apps/) so that relative paths
# to assets/ and src/ work regardless of the working directory.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure the src directory is on the Python path so that the kintaiyi package
# can be imported when running from the repository root (e.g. on Streamlit Cloud).
sys.path.insert(0, os.path.join(_REPO_ROOT, "src"))

# Add the apps/ directory to sys.path so that the custom_css module is importable.
_apps_dir = os.path.dirname(os.path.abspath(__file__))
if _apps_dir not in sys.path:
    sys.path.insert(0, _apps_dir)

import streamlit as st
import datetime
import pytz
from contextlib import contextmanager, redirect_stdout
from io import StringIO
import urllib.request
import urllib.error
import json
from kintaiyi import jieqi
from kintaiyi import kintaiyi
from kintaiyi import config
import cn2an
from cn2an import an2cn
from kintaiyi.taiyidict import tengan_shiji, su_dist
from kintaiyi.taiyimishu import taiyi_yingyang
from kintaiyi.historytext import chistory
import streamlit.components.v1 as components
from streamlit.components.v1 import html
import pandas as pd
from kintaiyi.cerebras_client import CerebrasClient, DEFAULT_MODEL as DEFAULT_CEREBRAS_MODEL, TokenQuotaExceededError
from kintaiyi.openai_client import OpenAIClient, DEFAULT_MODEL as DEFAULT_OPENAI_MODEL, TokenQuotaExceededError as OpenAITokenQuotaExceededError
from kintaiyi.openai_compatible_client import OpenAICompatibleClient, TokenQuotaExceededError as CompatibleTokenQuotaExceededError
from kintaiyi.game_theory import TaiyiGame, 主方策略列 as _gt_主方策略列, 客方策略列 as _gt_客方策略列
from custom_css import get_custom_css
import re


def render_changelog_html(md_text: str) -> str:
    """Parse update.md markdown and return styled HTML for the changelog timeline."""
    lines = md_text.splitlines()
    entries: list[dict] = []
    current: dict | None = None

    for line in lines:
        stripped = line.strip()
        # Match date headers like ### 【2026/04/19】
        m = re.match(r'^###\s*【(.+?)】\s*$', stripped)
        if m:
            if current:
                entries.append(current)
            current = {"date": m.group(1), "items": []}
            continue
        if current is None:
            continue
        if stripped.startswith('-----') or stripped == '---' or stripped == '':
            continue
        # Bullet items (with or without leading "- ")
        if stripped.startswith('- '):
            current["items"].append(stripped[2:].strip())
        elif re.match(r'^\d+\.\s', stripped):
            current["items"].append(re.sub(r'^\d+\.\s*', '', stripped))
        elif stripped:
            current["items"].append(stripped)

    if current:
        entries.append(current)

    # Build HTML
    html_parts = [
        '<div class="changelog-container">',
        '  <div class="changelog-header">',
        '    <h2>堅太乙排盤更新日誌</h2>',
        '    <div class="changelog-ornament">✦ ❖ ✦</div>',
        '  </div>',
        '  <div class="changelog-timeline">',
    ]
    for entry in entries:
        html_parts.append('    <div class="changelog-entry">')
        html_parts.append(f'      <div class="changelog-date">{entry["date"]}</div>')
        if entry["items"]:
            html_parts.append('      <ul class="changelog-items">')
            for item in entry["items"]:
                html_parts.append(f'        <li>{item}</li>')
            html_parts.append('      </ul>')
        html_parts.append('    </div>')
    html_parts.append('  </div>')
    html_parts.append('</div>')
    return '\n'.join(html_parts)


# --- i18n: Translation dictionaries ---
TRANSLATIONS = {
    "zh": {
        "page_title": "堅太乙 - 태을 포국",
        "lang_label": "언어 Language",
        "param_header": "포국 파라미터 설정",
        "year": "년",
        "month": "월",
        "day": "일",
        "hour": "시",
        "minute": "분",
        "chart_method": "기반 방식",
        "acc_years": "태을 적년수",
        "ten_essences": "태을 십정(十精)",
        "life_gender": "태을 명법 성별",
        "rotation_label": "전반(轉盤)",
        "instant_btn": "즉시반",
        "ai_settings": "AI 설정",
        "ai_provider": "AI 서비스 제공자",
        "ai_model": "AI 모델",
        "custom_provider_section": "사용자 정의 제공자 설정",
        "custom_provider_name": "이름",
        "custom_provider_api_mode": "API 모드",
        "custom_provider_api_mode_option": "OpenAI API 호환",
        "custom_provider_api_key": "API 키",
        "custom_provider_show_key": "키 표시",
        "custom_provider_check_btn": "확인",
        "custom_provider_api_host": "API 호스트",
        "custom_provider_api_path": "API 경로",
        "custom_provider_network_compat": "네트워크 호환성 개선",
        "custom_provider_models_label": "모델",
        "custom_provider_add_model": "+ 추가",
        "custom_provider_reset_models": "↺ 초기화",
        "custom_provider_fetch_models": "⟳ 가져오기",
        "custom_provider_no_models": "사용 가능한 모델 없음",
        "custom_provider_new_model_placeholder": "모델 이름 입력",
        "custom_provider_key_ok": "✅ 유효한 키",
        "custom_provider_key_fail": "❌ 유효하지 않은 키: {}",
        "custom_provider_fetch_ok": "✅ {}개 모델을 가져왔습니다",
        "custom_provider_fetch_fail": "❌ 가져오기 실패: {}",
        "custom_provider_api_key_missing": "사용자 정의 제공자 API 키를 입력해 주세요.",
        "custom_provider_host_missing": "API 호스트를 입력해 주세요.",
        "ai_custom_quota_exceeded": "⚠️ 사용자 정의 제공자 API 할당량이 소진되었거나 속도 제한 상태입니다. 잠시 후 다시 시도해 주세요.",
        "openai_api_key_label": "OpenAI API 키",
        "openai_api_key_placeholder": "OpenAI API 키를 입력하세요 (sk-...)",
        "openai_api_key_missing": "OpenAI API 키를 입력해 주세요.",
        "xai_api_key_label": "xAI API 키",
        "xai_api_key_placeholder": "xAI API 키를 입력하세요 (xai-...)",
        "xai_api_key_missing": "xAI API 키를 입력해 주세요.",
        "deepseek_api_key_label": "DeepSeek API 키",
        "deepseek_api_key_placeholder": "DeepSeek API 키를 입력하세요 (sk-...)",
        "deepseek_api_key_missing": "DeepSeek API 키를 입력해 주세요.",
        "qwen_api_key_label": "Qwen API 키",
        "qwen_api_key_placeholder": "통의천문(Qwen) API 키를 입력하세요",
        "qwen_api_key_missing": "Qwen API 키를 입력해 주세요.",
        "select_prompt": "시스템 프롬프트 선택",
        "select_prompt_help": "AI 모델에 사용할 시스템 프롬프트를 선택합니다. 태을 포국 결과 분석을 지도합니다",
        "edit_prompt": "시스템 프롬프트 편집",
        "edit_prompt_placeholder": "예: 당신은 태을신수 전문가입니다. 포국 데이터를 바탕으로 상세한 분석을 한국어로 제공하세요...",
        "update_prompt": "💾 프롬프트 업데이트",
        "delete_prompt": "❌ 프롬프트 삭제",
        "add_prompt_expander": "➕ 프롬프트 추가",
        "add_prompt_btn": "➕ 프롬프트 추가",
        "new_prompt_name": "새 프롬프트 이름",
        "new_prompt_content": "새 프롬프트 내용",
        "new_prompt_placeholder": "AI 분석 지시문을 입력하세요...",
        "prompt_exists": "프롬프트 이름 '{}'이(가) 이미 존재합니다.",
        "prompt_updated": "✅ 시스템 프롬프트 '{}'을(를) 업데이트했습니다!",
        "prompt_deleted": "✅ 시스템 프롬프트 '{}'을(를) 삭제했습니다!",
        "prompt_added": "✅ 시스템 프롬프트 '{}'을(를) 추가했습니다!",
        "advanced_settings": "🔧 고급 설정",
        "max_tokens": "최대 생성 Tokens",
        "max_tokens_help": "AI 응답의 최대 길이를 조절합니다",
        "temperature": "온도 (정확 vs. 창의)",
        "temperature_help": "낮은 값(예: 0.2)은 더 확정적이고, 높은 값(예: 0.8)은 더 무작위적입니다",
        "debug_mode": "🔍 디버그 모드",
        "debug_help": "session state 같은 디버그 정보를 표시합니다",
        "debug_info": "🐛 디버그 정보",
        # 탭
        "tab_chart": "🧮 태을 포국",
        "tab_instructions": "💬 사용 설명",
        "tab_history": "📜 국수 사례",
        "tab_disaster": "🔥 재이 통계",
        "tab_books": "📚 고서 목록",
        "tab_updates": "🆕 업데이트 로그",
        "tab_guide": "🚀 간반 요령",
        "tab_links": "🔗 링크",
        # Main content
        "explanation": "해석",
        "taiyi_life_title": "《태을명법(太乙命法)》:",
        "twelve_palaces": "【십이궁(十二宮) 분석】",
        "sixteen_gods": "【태을 십육신(十六神) 낙궁】",
        "sixteen_grades": "【태을 십육신(十六神) 상·중·하등】",
        "hexagram": "【치괘(值卦)】",
        "year_hex": "연괘(年卦):",
        "month_hex": "월괘(月卦):",
        "day_hex": "일괘(日卦):",
        "hour_hex": "시괘(時卦):",
        "minute_hex": "분괘(分卦):",
        "yang_nine": "【양구행한(陽九行限)】",
        "bai_liu": "【백육행한(百六行限)】",
        "taiyi_mishu": "《태을비서(太乙秘書)》:",
        "history_records": "사적 기록(史事記載):",
        "chart_analysis": "태을 반국(盤局) 분석:",
        "year_star_predict": "태세 치수 단사(太歲值宿斷事):",
        "start_star_predict": "시격 치수 단사(始擊值宿斷事):",
        "ten_stem_predict": "십천간 세·시격 낙궁 예측(十天干歲始擊落宮):",
        "sky_ground_method": "태을 재천외지내법(推太乙在天外地內法):",
        "three_five": "삼문오장(三門五將):",
        "home_away": "주객 상관 추산(推主客相關):",
        "win_loss": "소다로 승부 점침(推少多以占勝負):",
        "wind_cloud": "태을 풍운 비조 조전 추산(推太乙風雲飛鳥助戰):",
        "solitary": "고단으로 성패 점침(推孤單以占成敗):",
        "yin_yang_adversity": "음양으로 액회 점침(推陰陽以占厄會):",
        "emperor_tour": "천자 순수 시기술(明天子巡狩之期術):",
        "ruler_base": "군기 태을 소주술(明君基太乙所主術):",
        "minister_base": "신기 태을 소주술(明臣基太乙所主術):",
        "people_base": "민기 태을 소주술(明民基太乙所主術):",
        "five_blessings": "오복 태을 소주술(明五福太乙所主術):",
        "five_blessings_calc": "오복 길산 소주술(明五福吉算所主術):",
        "heaven_yi": "천을 태을 소주술(明天乙太乙所主術):",
        "earth_yi": "지을 태을 소주술(明地乙太乙所主術):",
        "zhifu": "치부 태을 소주술(明值符太乙所主術):",
        # AI
        "ai_analyze_btn": "🔍 AI로 포국 결과 분석",
        "ai_analyzing": "AI가 태을 포국 결과를 분석하는 중...",
        "ai_key_missing": "CEREBRAS_API_KEY가 설정되지 않았습니다. .streamlit/secrets.toml 또는 환경 변수에 설정해 주세요.",
        "ai_error": "AI 호출 중 오류가 발생했습니다: {}",
        "ai_quota_exceeded": "⚠️ Cerebras API 일일 토큰 할당량이 소진되었습니다. 잠시 후 다시 시도하거나 「최대 생성 Tokens」 설정을 낮춰 주세요.",
        "ai_openai_quota_exceeded": "⚠️ OpenAI API 할당량이 소진되었거나 속도 제한 상태입니다. 잠시 후 다시 시도해 주세요.",
        "ai_xai_quota_exceeded": "⚠️ xAI API 할당량이 소진되었거나 속도 제한 상태입니다. 잠시 후 다시 시도해 주세요.",
        "ai_deepseek_quota_exceeded": "⚠️ DeepSeek API 할당량이 소진되었거나 속도 제한 상태입니다. 잠시 후 다시 시도해 주세요.",
        "ai_qwen_quota_exceeded": "⚠️ Qwen API 할당량이 소진되었거나 속도 제한 상태입니다. 잠시 후 다시 시도해 주세요.",
        "gen_error": "반국 생성 중 오류가 발생했습니다: {}",
        "ai_result": "AI 분석 결과",
        "list_label": "목록",
        "save_error": "프롬프트 저장 중 오류: {}",
        # Chat
        "chat_header": "💬 AI 대화",
        "chat_placeholder": "질문을 입력해 태을 AI 대가와 대화하세요...",
        "chat_thinking": "AI가 생각하는 중...",
        "chat_welcome": "안녕하세요! 저는 태을 AI 어시스턴트입니다. 태을신수에 관한 질문에 답해드릴 수 있어요. 질문을 입력해 주세요.",
        "chat_clear": "🗑️ 대화 지우기",
        # 운주 박지론
        "game_theory_toggle": "🎯 운주 박지(博弈) 분석 활성화 (Nash 균형)",
        "game_theory_header": "⚔️ 운주 박지 분석 (태을 고법 × Nash 균형)",
        "game_theory_payoff": "제로섬 보수 행렬 (주방 시점)",
        "game_theory_home_strategy": "주방 최적 혼합 전략",
        "game_theory_away_strategy": "객방 최적 혼합 전략",
        "game_theory_value": "박지 균형값 (기대 보수)",
        "game_theory_lp": "선형 계획 최적 제안",
        "game_theory_winrate": "주방 승률 판단",
        "game_theory_computing": "⚙️ Nash 균형을 계산하는 중...",
        # 출력 라벨
        "lunar_label": "음력",
        "taiyi_life_method": "태을명법",
        "epoch_label": "기원",
        "home_calc": "주산(主筭)",
        "away_calc": "객산(客筭)",
        "set_calc": "정산(定筭)",
        "five_yuan": "오자원국(五子元局)",
        "acc_prefix": "적",
        "acc_suffix": "수",
    },
    "en": {
        "page_title": "KinTaiYi - Taiyi Divination Chart",
        "lang_label": "語言 Language",
        "param_header": "Chart Parameters",
        "year": "Year",
        "month": "Month",
        "day": "Day",
        "hour": "Hour",
        "minute": "Minute",
        "chart_method": "Chart Method",
        "acc_years": "Accumulated Years",
        "ten_essences": "Taiyi Ten Essences",
        "life_gender": "Life Method Gender",
        "rotation_label": "Rotation",
        "instant_btn": "Instant Chart",
        "ai_settings": "AI Settings",
        "ai_provider": "AI Provider",
        "ai_model": "AI Model",
        "custom_provider_section": "Custom Provider Settings",
        "custom_provider_name": "Name",
        "custom_provider_api_mode": "API Mode",
        "custom_provider_api_mode_option": "OpenAI API Compatible",
        "custom_provider_api_key": "API Key",
        "custom_provider_show_key": "Show Key",
        "custom_provider_check_btn": "Check",
        "custom_provider_api_host": "API Host",
        "custom_provider_api_path": "API Path",
        "custom_provider_network_compat": "Improve Network Compatibility",
        "custom_provider_models_label": "Models",
        "custom_provider_add_model": "+ Add",
        "custom_provider_reset_models": "↺ Reset",
        "custom_provider_fetch_models": "⟳ Fetch",
        "custom_provider_no_models": "No available models",
        "custom_provider_new_model_placeholder": "Enter model name",
        "custom_provider_key_ok": "✅ Key is valid",
        "custom_provider_key_fail": "❌ Key invalid: {}",
        "custom_provider_fetch_ok": "✅ Fetched {} model(s)",
        "custom_provider_fetch_fail": "❌ Fetch failed: {}",
        "custom_provider_api_key_missing": "Please enter the custom provider API key.",
        "custom_provider_host_missing": "Please enter the API host.",
        "ai_custom_quota_exceeded": "⚠️ Custom provider API quota exceeded or rate-limited. Please try again later.",
        "openai_api_key_label": "OpenAI API Key",
        "openai_api_key_placeholder": "Enter your OpenAI API key (sk-...)",
        "openai_api_key_missing": "Please enter your OpenAI API key.",
        "xai_api_key_label": "xAI API Key",
        "xai_api_key_placeholder": "Enter your xAI API key (xai-...)",
        "xai_api_key_missing": "Please enter your xAI API key.",
        "deepseek_api_key_label": "DeepSeek API Key",
        "deepseek_api_key_placeholder": "Enter your DeepSeek API key (sk-...)",
        "deepseek_api_key_missing": "Please enter your DeepSeek API key.",
        "qwen_api_key_label": "Qwen API Key",
        "qwen_api_key_placeholder": "Enter your Qwen (DashScope) API key",
        "qwen_api_key_missing": "Please enter your Qwen API key.",
        "select_prompt": "Select System Prompt",
        "select_prompt_help": "Select a system prompt for the AI model to guide Taiyi chart analysis",
        "edit_prompt": "Edit System Prompt",
        "edit_prompt_placeholder": "Example: You are a Taiyi expert, provide detailed analysis based on chart data...",
        "update_prompt": "💾 Update Prompt",
        "delete_prompt": "❌ Delete Prompt",
        "add_prompt_expander": "➕ Add Prompt",
        "add_prompt_btn": "➕ Add Prompt",
        "new_prompt_name": "New Prompt Name",
        "new_prompt_content": "New Prompt Content",
        "new_prompt_placeholder": "Enter AI analysis instructions...",
        "prompt_exists": "Prompt name '{}' already exists.",
        "prompt_updated": "✅ Updated system prompt '{}'!",
        "prompt_deleted": "✅ Deleted system prompt '{}'!",
        "prompt_added": "✅ Added system prompt '{}'!",
        "advanced_settings": "🔧 Advanced Settings",
        "max_tokens": "Max Generation Tokens",
        "max_tokens_help": "Control the maximum length of AI responses",
        "temperature": "Temperature (Focus vs. Creative)",
        "temperature_help": "Lower values (e.g. 0.2) more deterministic; higher values (e.g. 0.8) more random",
        "debug_mode": "🔍 Debug Mode",
        "debug_help": "Show debug info such as session state",
        "debug_info": "🐛 Debug Info",
        # Tabs
        "tab_chart": "🧮 Taiyi Chart",
        "tab_instructions": "💬 Instructions",
        "tab_history": "📜 Historical Examples",
        "tab_disaster": "🔥 Disaster Statistics",
        "tab_books": "📚 Ancient Books",
        "tab_updates": "🆕 Update Log",
        "tab_guide": "🚀 Chart Guide",
        "tab_links": "🔗 Links",
        # Main content
        "explanation": "Explanation",
        "taiyi_life_title": "Taiyi Life Method:",
        "twelve_palaces": "[Twelve Palaces Analysis]",
        "sixteen_gods": "[Taiyi Sixteen Gods Palace Positions]",
        "sixteen_grades": "[Taiyi Sixteen Gods Grades]",
        "hexagram": "[Hexagrams]",
        "year_hex": "Year Hexagram: ",
        "month_hex": "Month Hexagram: ",
        "day_hex": "Day Hexagram: ",
        "hour_hex": "Hour Hexagram: ",
        "minute_hex": "Minute Hexagram: ",
        "yang_nine": "[Yang Nine Cycle Limit]",
        "bai_liu": "[Bai Liu Cycle Limit]",
        "taiyi_mishu": "Taiyi Secret Book:",
        "history_records": "Historical Records:",
        "chart_analysis": "Taiyi Chart Analysis:",
        "year_star_predict": "Year Star Prediction: ",
        "start_star_predict": "Start Strike Star Prediction: ",
        "ten_stem_predict": "Ten Stems Start Strike Prediction: ",
        "sky_ground_method": "Taiyi Sky-Ground Method: ",
        "three_five": "Three Doors & Five Generals: ",
        "home_away": "Home vs Away Analysis: ",
        "win_loss": "Win-Loss Prediction: ",
        "wind_cloud": "Wind-Cloud Battle Support: ",
        "solitary": "Solitary Success-Failure: ",
        "yin_yang_adversity": "Yin-Yang Adversity: ",
        "emperor_tour": "Emperor Tour Period: ",
        "ruler_base": "Ruler Base Method: ",
        "minister_base": "Minister Base Method: ",
        "people_base": "People Base Method: ",
        "five_blessings": "Five Blessings Method: ",
        "five_blessings_calc": "Five Blessings Calculation: ",
        "heaven_yi": "Heaven Yi Method: ",
        "earth_yi": "Earth Yi Method: ",
        "zhifu": "Zhifu Method: ",
        # AI
        "ai_analyze_btn": "🔍 Analyze with AI",
        "ai_analyzing": "AI is analyzing the Taiyi chart...",
        "ai_key_missing": "CEREBRAS_API_KEY not set. Please set it in .streamlit/secrets.toml or environment variables.",
        "ai_error": "Error calling AI: {}",
        "ai_quota_exceeded": "⚠️ Cerebras API daily token quota exceeded. Please try again later or reduce the 'Max Generation Tokens' setting.",
        "ai_openai_quota_exceeded": "⚠️ OpenAI API quota exceeded or rate-limited. Please try again later.",
        "ai_xai_quota_exceeded": "⚠️ xAI API quota exceeded or rate-limited. Please try again later.",
        "ai_deepseek_quota_exceeded": "⚠️ DeepSeek API quota exceeded or rate-limited. Please try again later.",
        "ai_qwen_quota_exceeded": "⚠️ Qwen API quota exceeded or rate-limited. Please try again later.",
        "gen_error": "Error generating chart: {}",
        "ai_result": "AI Analysis Result",
        "list_label": "List",
        "save_error": "Error saving prompt: {}",
        # Chat
        "chat_header": "💬 AI Chat",
        "chat_placeholder": "Ask a question to the Taiyi AI master...",
        "chat_thinking": "AI is thinking...",
        "chat_welcome": "Hello! I'm the Taiyi AI assistant. Feel free to ask me anything about Taiyi divination.",
        "chat_clear": "🗑️ Clear Chat",
        # Game Theory
        "game_theory_toggle": "🎯 Enable Game Theory Analysis (Nash Equilibrium)",
        "game_theory_header": "⚔️ Operations Research & Game Theory Analysis",
        "game_theory_payoff": "Zero-Sum Payoff Matrix (Home Perspective)",
        "game_theory_home_strategy": "Home Optimal Mixed Strategy",
        "game_theory_away_strategy": "Away Optimal Mixed Strategy",
        "game_theory_value": "Game Value (Expected Payoff)",
        "game_theory_lp": "LP Optimal Recommendation",
        "game_theory_winrate": "Home Win Assessment",
        "game_theory_computing": "⚙️ Computing Nash Equilibrium...",
        # Print labels
        "lunar_label": "Lunar",
        "taiyi_life_method": "Taiyi Life",
        "epoch_label": "Epoch",
        "home_calc": "Home Calc",
        "away_calc": "Away Calc",
        "set_calc": "Set Calc",
        "five_yuan": "Five Yuan Cycle",
        "acc_prefix": "Acc. ",
        "acc_suffix": " Count",
    },
}

OPTION_LABELS = {
    "en": {
        "時計太乙": "Hourly Taiyi",
        "年計太乙": "Yearly Taiyi",
        "月計太乙": "Monthly Taiyi",
        "日計太乙": "Daily Taiyi",
        "分計太乙": "Minute Taiyi",
        "太乙命法": "Taiyi Life Method",
        "太乙統宗": "Taiyi Tongzong",
        "太乙金鏡": "Taiyi Jinjing",
        "太乙淘金歌": "Taiyi Taojin Song",
        "太乙局": "Taiyi Bureau",
        "有": "Yes",
        "無": "No",
        "男": "Male",
        "女": "Female",
        "固定": "Fixed",
        "轉動": "Rotating",
    },
    "zh": {
        "時計太乙": "시계 태을(時計)",
        "年計太乙": "연계 태을(年計)",
        "月計太乙": "월계 태을(月計)",
        "日計太乙": "일계 태을(日計)",
        "分計太乙": "분계 태을(分計)",
        "太乙命法": "태을명법(太乙命法)",
        "太乙統宗": "태을통종(太乙統宗)",
        "太乙金鏡": "태을금경(太乙金鏡)",
        "太乙淘金歌": "태을도금가(太乙淘金歌)",
        "太乙局": "태을국(太乙局)",
        "有": "있음",
        "無": "없음",
        "男": "남성",
        "女": "여성",
        "固定": "고정",
        "轉動": "회전",
    },
}

def t(key):
    """현재 언어에 맞는 UI 텍스트를 반환한다."""
    lang = st.session_state.get("lang", "zh")
    return TRANSLATIONS.get(lang, TRANSLATIONS["zh"]).get(key, key)

def to(option):
    """셀렉트박스 옵션 값을 표시용으로 변환한다."""
    lang = st.session_state.get("lang", "zh")
    return OPTION_LABELS.get(lang, {}).get(option, option)

# Cerebras Model Options
# Maximum number of recent chat messages to include as context for the LLM
_MAX_CHAT_HISTORY = 20

CEREBRAS_MODEL_OPTIONS = [
    "qwen-3-235b-a22b-instruct-2507",
    "gpt-oss-120b",
    "llama3.1-8b",
    "zai-glm-4.7",
]
CEREBRAS_MODEL_DESCRIPTIONS = {
    "gpt-oss-120b": "Cerebras: High-capacity open-source model for complex tasks.",
    "llama3.1-8b": "Cerebras: Light and fast for quick tasks.",
    "zai-glm-4.7": "Cerebras: GLM-based model for versatile analysis.",
    "qwen-3-235b-a22b-instruct-2507": "Cerebras: Fast inference, great for rapid iteration.",
}

OPENAI_MODEL_OPTIONS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1",
    "gpt-4.1-mini",
    "o4-mini",
]
OPENAI_MODEL_DESCRIPTIONS = {
    "gpt-4o-mini": "OpenAI: Affordable and capable for most tasks.",
    "gpt-4o": "OpenAI: Most capable multimodal model.",
    "gpt-4.1": "OpenAI: Latest GPT-4.1 model.",
    "gpt-4.1-mini": "OpenAI: Fast and cost-effective GPT-4.1 mini.",
    "o4-mini": "OpenAI: Compact reasoning model.",
}

# xAI (Grok) Model Options
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL_OPTIONS = [
    "grok-3",
    "grok-3-mini",
    "grok-2-1212",
]
XAI_MODEL_DESCRIPTIONS = {
    "grok-3": "xAI: Most capable Grok model for complex reasoning.",
    "grok-3-mini": "xAI: Fast and cost-effective Grok model.",
    "grok-2-1212": "xAI: Previous-generation Grok model.",
}

# DeepSeek Model Options
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL_OPTIONS = [
    "deepseek-chat",
    "deepseek-reasoner",
]
DEEPSEEK_MODEL_DESCRIPTIONS = {
    "deepseek-chat": "DeepSeek: V3 model, fast and capable for most tasks.",
    "deepseek-reasoner": "DeepSeek: R1 reasoning model for complex analysis.",
}

# Qwen (Alibaba DashScope) Model Options
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL_OPTIONS = [
    "qwen-max",
    "qwen-plus",
    "qwen-turbo",
    "qwen-long",
]
QWEN_MODEL_DESCRIPTIONS = {
    "qwen-max": "Qwen: Most capable Qwen model for complex tasks.",
    "qwen-plus": "Qwen: Balanced performance and cost.",
    "qwen-turbo": "Qwen: Fast and lightweight.",
    "qwen-long": "Qwen: Optimized for long-context tasks.",
}

# System Prompt Management Functions
def load_system_prompts():
    SYSTEM_PROMPTS_FILE = os.path.join(_REPO_ROOT, "assets", "system_prompts.json")
    DEFAULT_SYSTEM_PROMPT = (
        "당신은 《태을비서(太乙秘書)》, 《태을명법(太乙命法)》의 역사 사례에 정통한 태을신수 대가입니다. 제공된 태을 포국 데이터를 바탕으로 다음을 수행하세요:\n"
        "1. 반국(盤局)의 핵심 요소(주산·객산·시격·태세 등)를 설명합니다.\n"
        "2. 《태을비서(太乙秘書)》의 이론에 결합하여 반국의 길흉과 잠재적 영향을 분석합니다.\n"
        "3. 태을명법인 경우, 명주(命主)의 운세와 인생 흐름을 평가합니다.\n"
        "4. 실용적인 조언이나 대응 전략을 제시합니다.\n"
        "명확한 구조(단락·제목)로 제시하고, 전문적이면서도 이해하기 쉬운 한국어로 작성하며, 역사 사례나 고전 이론을 적절히 인용하세요."
    )
    
    try:
        with open(SYSTEM_PROMPTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default_data = {
            "prompts": [
                {
                    "name": "태을 대가",
                    "content": DEFAULT_SYSTEM_PROMPT
                }
            ],
            "selected": "태을 대가"
        }
        with open(SYSTEM_PROMPTS_FILE, "w") as f:
            json.dump(default_data, f, indent=2)
        return default_data

def save_system_prompts(prompts_data):
    SYSTEM_PROMPTS_FILE = os.path.join(_REPO_ROOT, "assets", "system_prompts.json")
    try:
        with open(SYSTEM_PROMPTS_FILE, "w") as f:
            json.dump(prompts_data, f, indent=2)
        return True
    except Exception as e:
        st.error(t("save_error").format(e))
        return False

# Initialize session state to control rendering
if 'render_default' not in st.session_state:
    st.session_state.render_default = True

@st.cache_data
def get_file_content_as_string(base_url, path):
    """從指定 URL 獲取文件內容並返回字符串"""
    url = base_url + path
    try:
        response = urllib.request.urlopen(url)
        return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return f"⚠️ 無法載入內容 ({url}): HTTP {e.code}"
    except Exception as e:
        return f"⚠️ 無法載入內容 ({url}): {e}"

def format_text(d, parent_key=""):
    """格式化字典為可讀的文本"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(format_text(v, new_key + ":").splitlines())
        elif isinstance(v, list):
            items.append(f"{new_key}: {', '.join(map(str, v))}")
        else:
            items.append(f"{new_key}: {v}")
    return "\n\n".join(items) + "\n\n"

def format_taiyi_results_for_prompt(results):
    """Format Taiyi calculation results into a prompt for the AI model."""
    prompt_lines = [
        "以下是太乙排盤的計算結果，請根據這些數據提供詳細的分析和解釋：",
        f"日期時間: {results['gz']} (農曆: {results['lunard']})",
        f"紀元: {results['ttext'].get('紀元', '無')}",
        f"局式: {results['ttext'].get('局式', {}).get('年', '無')}",
        f"太乙計: {config.ty_method(results['tn'])}{results['ttext'].get('太乙計', '')}",
        f"文: {results['kook'].get('文', '無')}",
        f"數: {results['kook_num']}",
        f"主筭: {results['homecal']}, 客筭: {results['awaycal']}, 定筭: {results['setcal']}",
        f"始擊值宿: {results['sj_su_predict']}",
        f"十天干歲始擊落宮: {results['tg_sj_su_predict']}",
        f"太歲值宿: {results['year_predict']}",
        f"三門五將: {results['three_door']} {results['five_generals']}",
        #f"推太乙在天外地內法: {results['ty'].ty_gong_dist(results['style'], results['tn'])}",
        f"推少多以占勝負: {results['ttext'].get('推少多以占勝負', '無')}",
        f"推太乙風雲飛鳥助戰: {results['home_vs_away3']}",
        f"《太乙秘書》: {results['ts']}",
        f"史事記載: {results['ch']}",
    ]
    if results["style"] == 5:  # 太乙命法
        prompt_lines.extend([
            f"命法性別: {results['zhao']} ({results['sex_o']})",
            f"十二宮分析: {results['lifedisc']}",
            f"太乙十六神落宮: {results['lifedisc2']}",
        ])
    return "\n\n".join(prompt_lines)

def render_svg(svg, num):
    """渲染交互式 SVG 圖表，針對 id='layer4' 和 id='layer6' 的 <g> 標籤進行順時針或逆時針旋轉，支援按住滑鼠旋轉並移除殘影"""
    if not svg or 'svg' not in svg.lower():
        st.error("Invalid SVG content provided")
        return
    
    js_code = """
    const rotations = { "layer4": 0, "layer6": 0 };

    function rotateLayer(layer, deltaAngle) {
      if (!layer || !layer.getAttribute) {
        console.error("層元素無效");
        return;
      }
      const id = layer.getAttribute('id');
      if (!id || rotations[id] === undefined) {
        console.error(`未找到 ${id} 的旋轉數據`);
        return;
      }
      rotations[id] += deltaAngle;
      const newRotation = rotations[id] % 360;
      console.log(`計算 newRotation 為 ${id}: ${newRotation}, 累計旋轉: ${rotations[id]}`);

      const bbox = layer.getBBox();
      const centerX = bbox.x + bbox.width / 2;
      const centerY = bbox.y + bbox.height / 2;
      const transformValue = "rotate(" + newRotation + " " + centerX + " " + centerY + ")";
      layer.setAttribute("transform", transformValue);

      layer.querySelectorAll("text").forEach(text => {
        if (!text || !text.getAttribute) return;
        const x = parseFloat(text.getAttribute("x") || 0);
        const y = parseFloat(text.getAttribute("y") || 0);
        if (isNaN(x) || isNaN(y)) return;
        const textTransform = "rotate(" + (-newRotation) + " " + x + " " + y + ")";
        text.setAttribute("transform", textTransform);
      });
      console.log(`旋轉 ${id} 至 ${newRotation}°，中心 (${centerX}, ${centerY})`);
    }

    function setupEventListeners() {
      ["layer4", "layer6"].forEach(id => {
        const layer = document.querySelector("#" + id);
        if (layer) {
          layer.style.pointerEvents = "all";
          layer.style.cursor = "pointer";

          let isRotating = false;
          let startX = 0;

          layer.addEventListener("mousedown", (event) => {
            event.preventDefault();
            event.stopPropagation();
            isRotating = true;
            startX = event.clientX;
            const bbox = layer.getBBox();
            console.log(`mousedown on ${id}, startX: ${startX}, clientX: ${event.clientX}, clientY: ${event.clientY}, bbox:`, bbox);
          });

          layer.addEventListener("mousemove", (event) => {
            if (isRotating) {
              event.preventDefault();
              event.stopPropagation();
              const deltaX = event.clientX - startX;
              const deltaAngle = deltaX * 1.0;
              rotateLayer(layer, deltaAngle);
              startX = event.clientX;
              console.log(`mousemove on ${id}, deltaX: ${deltaX}, deltaAngle: ${deltaAngle}`);
            }
          });

          layer.addEventListener("mouseup", (event) => {
            event.preventDefault();
            event.stopPropagation();
            isRotating = false;
            console.log(`mouseup on ${id}`);
          });

          layer.addEventListener("mouseleave", () => {
            isRotating = false;
            console.log(`mouseleave on ${id}`);
          });

          layer.addEventListener("click", (event) => {
            if (!isRotating) {
              event.preventDefault();
              event.stopPropagation();
              const direction = Math.random() < 0.5 ? 30 : -30;
              rotateLayer(layer, direction);
              console.log(`click on ${id}, direction: ${direction}°`);
            }
          });
          console.log(`事件監聽器已為 ${id} 添加, layer found:`, layer);
        } else {
          console.error(`未找到 id='${id}' 的 <g> 元素`);
        }
      });
    }

    requestAnimationFrame(() => {
      setupEventListeners();
      console.log("SVG 渲染完成，事件監聽器已設置");
    });

    window.addEventListener("load", () => {
      console.log("SVG 已完全載入");
      ["layer4", "layer6"].forEach(id => {
        const layer = document.querySelector("#" + id);
        if (layer) console.log(`找到 ${id}，準備旋轉`);
        else console.error(`載入後仍未找到 ${id}`);
      });
    });
    """

    html_content = f"""
    <div style="margin: 0; padding: 0;">
      <svg id="interactive-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num} {num}" width="100%" height="auto" style="max-height: 400px; display: block; margin: 0 auto;">
        {svg}
      </svg>
      <script>
        {js_code}
      </script>
    </div>
    <style>
        #interactive-svg {{
            margin-top: 10px;
            margin-bottom: 10px;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            outline: none;
            -webkit-tap-highlight-color: transparent;
            touch-action: none;
        }}
        #interactive-svg * {{
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            outline: none;
        }}
        .stCodeBlock {{
            margin-bottom: 10px !important;
        }}
    </style>
    """
    html(html_content, height=num)
    
def render_svg1(svg, num):
    """渲染靜態 SVG 圖表（可點擊同時著色第二、三、四層的十六分之一部分）"""
    if not svg or 'svg' not in svg.lower():
        st.error("Invalid SVG content provided")
        return
    
    js_script = """
    <script>
        const coloredGroups = new Set();
        let currentColors = [];

        function getRandomColor() {
            const letters = '0123456789ABCDEF';
            let color = '#';
            for (let i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        }

        function generateFourColors() {
            let colors = [];
            for (let i = 0; i < 4; i++) {
                let newColor = getRandomColor();
                while (colors.includes(newColor)) {
                    newColor = getRandomColor();
                }
                colors.push(newColor);
            }
            return colors;
        }

        const allGroups = document.querySelectorAll('#static-svg g');
        const targetLayers = [];
        allGroups.forEach((group, groupIndex) => {
            const segments = group.querySelectorAll('path, polygon, rect');
            if (segments.length > 0) {
                targetLayers.push({ group: group, index: groupIndex, segments: Array.from(segments) });
            }
        });

        console.log('Found ' + targetLayers.length + ' layers with segments:', targetLayers.map(l => ({ index: l.index, segmentCount: l.segments.length })));

        if (targetLayers.length >= 4) {
            const layersToColor = [targetLayers[1], targetLayers[2], targetLayers[3]];

            layersToColor.forEach((layer, layerNum) => {
                layer.segments.forEach((segment, index) => {
                    segment.style.cursor = 'pointer';
                    segment.style.pointerEvents = 'all';
                    segment.style.zIndex = '10';
                    segment.setAttribute('data-index', index);
                    segment.setAttribute('data-layer', layerNum);
                    segment.addEventListener('click', function(event) {
                        event.stopPropagation();
                        const segmentIndex = parseInt(segment.getAttribute('data-index'));
                        const groupId = `group_${segmentIndex}`;

                        console.log(`Clicked segment in layer ${parseInt(segment.getAttribute('data-layer')) + 2}, index: ${segmentIndex}`);

                        const isColored = coloredGroups.has(groupId);

                        if (isColored) {
                            layersToColor.forEach(l => {
                                if (l.segments[segmentIndex]) {
                                    l.segments[segmentIndex].removeAttribute('fill');
                                }
                            });
                            coloredGroups.delete(groupId);
                        } else if (coloredGroups.size < 4) {
                            if (coloredGroups.size === 0 || currentColors.length === 0) {
                                currentColors = generateFourColors();
                                console.log('Generated new colors:', currentColors);
                            }
                            const colorToUse = currentColors[coloredGroups.size];
                            layersToColor.forEach(l => {
                                if (l.segments[segmentIndex]) {
                                    l.segments[segmentIndex].setAttribute('fill', colorToUse);
                                }
                            });
                            coloredGroups.add(groupId);
                            if (coloredGroups.size === 4) {
                                currentColors = [];
                            }
                        }
                    });
                });
            });
        } else {
            console.error('Not enough layers found. Found only ' + targetLayers.length + ' layers.');
        }
    </script>
    """

    html_content = f"""
    <div style="margin: 0; padding: 0;">
      <svg id="static-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num} {num}" width="100%" height="auto" style="max-height: 400px; display: block; margin: 0 auto;">
        {svg}
      </svg>
      {js_script}
    </div>
    <style>
        #static-svg {{ 
            margin-top: 10px;
            margin-bottom: 10px;
        }}
        #static-svg path, #static-svg polygon, #static-svg rect {{
            pointer-events: all !important;
            z-index: 10 !important;
        }}
        .stCodeBlock {{
            margin-bottom: 10px !important;
        }}
    </style>
    """
    html(html_content, height=num)

def timeline(data, height=800):
    """渲染時間線組件"""
    if isinstance(data, str):
        data = json.loads(data)
    json_text = json.dumps(data)
    source_param = 'timeline_json'
    source_block = f'var {source_param} = {json_text};'
    cdn_path = 'https://cdn.knightlab.com/libs/timeline3/latest'
    css_block = f'<link title="timeline-styles" rel="stylesheet" href="{cdn_path}/css/timeline.css">'
    js_block = f'<script src="{cdn_path}/js/timeline.js"></script>'
    htmlcode = f'''
        {css_block}
        {js_block}
        <div id='timeline-embed' style="width: 95%; height: {height}px; margin: 1px;"></div>
        <script type="text/javascript">
            var additionalOptions = {{ start_at_end: false, is_embed: true, default_bg_color: {{r:14, g:17, b:23}} }};
            {source_block}
            timeline = new TL.Timeline('timeline-embed', {source_param}, additionalOptions);
        </script>
    '''
    components.html(htmlcode, height=height)

@contextmanager
def st_capture(output_func):
    """捕獲 stdout 並將其傳遞給指定的輸出函數"""
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write
        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret
        stdout.write = new_write
        yield

# Initialize language in session state
if "lang" not in st.session_state:
    st.session_state.lang = "zh"

# Streamlit 頁面配置
st.set_page_config(
    layout="wide",
    page_title=t("page_title"),
    page_icon=os.path.join(_REPO_ROOT, "assets", "icon.jpg")
)
# Inject Chinese classical theme CSS globally
st.markdown(get_custom_css(), unsafe_allow_html=True)
# 定義基礎 URL
BASE_URL_KINTAIYI = 'https://raw.githubusercontent.com/kentang2017/kintaiyi/master/'
BASE_URL_KINLIUREN = 'https://raw.githubusercontent.com/kentang2017/kinliuren/master/'

# 側邊欄輸入
with st.sidebar:
    lang_choice = st.selectbox(
        "언어 Language",
        ["한국어", "English"],
        index=0 if st.session_state.lang == "zh" else 1,
        key="lang_select",
    )
    new_lang = "zh" if lang_choice == "한국어" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.header(t("param_header"))
    
    now = datetime.datetime.now(pytz.timezone('Asia/Hong_Kong'))
    col1, col2 = st.columns(2)
    with col1:
        my = st.number_input(t("year"), min_value=0, max_value=2100, value=now.year, key="year")
        mm = st.number_input(t("month"), min_value=1, max_value=12, value=now.month, key="month")
        md = st.number_input(t("day"), min_value=1, max_value=31, value=now.day, key="day")
    with col2:
        mh = st.number_input(t("hour"), min_value=0, max_value=23, value=now.hour, key="hour")
        mmin = st.number_input(t("minute"), min_value=0, max_value=59, value=now.minute, key="minute")
    
    option = st.selectbox(t("chart_method"), ('時計太乙', '年計太乙', '月計太乙', '日計太乙', '分計太乙', '太乙命法'), format_func=to)
    acum = st.selectbox(t("acc_years"), ('太乙統宗', '太乙金鏡', '太乙淘金歌', '太乙局'), format_func=to)
    ten_ching = st.selectbox(t("ten_essences"), ('無', '有'), format_func=to)
    sex_o = st.selectbox(t("life_gender"), ('男', '女'), format_func=to)
    rotation = st.selectbox(t("rotation_label"), ('固定', '轉動'), format_func=to)
    
    num_dict = {'時計太乙': 3, '年計太乙': 0, '月計太乙': 1, '日計太乙': 2, '分計太乙': 4, '太乙命法': 5}
    style = num_dict[option]
    tn_dict = {'太乙統宗': 0, '太乙金鏡': 1, '太乙淘金歌': 2, '太乙局': 3}
    tn = tn_dict[acum]
    tc_dict = {'有': 1, '無': 0}
    tc = tc_dict[ten_ching]
    
    instant = st.button(t("instant_btn"), use_container_width=True)
    
    st.markdown("---")
    st.header(t("ai_settings"))

    ai_provider = st.selectbox(
        t("ai_provider"),
        options=["Cerebras", "OpenAI", "xAI (Grok)", "DeepSeek", "Qwen", "사용자 정의"],
        index=0,
        key="ai_provider_selector",
    )

    if ai_provider == "OpenAI":
        openai_api_key_input = st.text_input(
            t("openai_api_key_label"),
            type="password",
            placeholder=t("openai_api_key_placeholder"),
            key="openai_api_key_input",
        )
        selected_model = st.selectbox(
            t("ai_model"),
            options=OPENAI_MODEL_OPTIONS,
            index=0,
            key="openai_model_selector",
            help="\n".join(f"• {k}: {v}" for k, v in OPENAI_MODEL_DESCRIPTIONS.items())
        )
    elif ai_provider == "xAI (Grok)":
        openai_api_key_input = ""
        st.text_input(
            t("xai_api_key_label"),
            type="password",
            placeholder=t("xai_api_key_placeholder"),
            key="xai_api_key_input",
        )
        selected_model = st.selectbox(
            t("ai_model"),
            options=XAI_MODEL_OPTIONS,
            index=0,
            key="xai_model_selector",
            help="\n".join(f"• {k}: {v}" for k, v in XAI_MODEL_DESCRIPTIONS.items())
        )
    elif ai_provider == "DeepSeek":
        openai_api_key_input = ""
        st.text_input(
            t("deepseek_api_key_label"),
            type="password",
            placeholder=t("deepseek_api_key_placeholder"),
            key="deepseek_api_key_input",
        )
        selected_model = st.selectbox(
            t("ai_model"),
            options=DEEPSEEK_MODEL_OPTIONS,
            index=0,
            key="deepseek_model_selector",
            help="\n".join(f"• {k}: {v}" for k, v in DEEPSEEK_MODEL_DESCRIPTIONS.items())
        )
    elif ai_provider == "Qwen":
        openai_api_key_input = ""
        st.text_input(
            t("qwen_api_key_label"),
            type="password",
            placeholder=t("qwen_api_key_placeholder"),
            key="qwen_api_key_input",
        )
        selected_model = st.selectbox(
            t("ai_model"),
            options=QWEN_MODEL_OPTIONS,
            index=0,
            key="qwen_model_selector",
            help="\n".join(f"• {k}: {v}" for k, v in QWEN_MODEL_DESCRIPTIONS.items())
        )
    elif ai_provider == "사용자 정의":
        # ── Custom provider settings ──────────────────────────────
        if "custom_provider_models" not in st.session_state:
            st.session_state.custom_provider_models = []

        st.text_input(
            t("custom_provider_name"),
            key="custom_provider_name",
            placeholder="사용자 정의 제공자",
        )
        st.selectbox(
            t("custom_provider_api_mode"),
            options=[t("custom_provider_api_mode_option")],
            key="custom_provider_api_mode",
        )

        # API key with show/hide and validate button
        show_key = st.toggle(t("custom_provider_show_key"), key="custom_provider_show_key", value=False)
        col_key, col_check = st.columns([3, 1])
        with col_key:
            st.text_input(
                t("custom_provider_api_key"),
                type="text" if show_key else "password",
                key="custom_provider_api_key",
            )
        with col_check:
            st.markdown("<br>", unsafe_allow_html=True)
            check_key_btn = st.button(t("custom_provider_check_btn"), key="custom_provider_check_key_btn", use_container_width=True)

        if check_key_btn:
            _ckey = st.session_state.get("custom_provider_api_key", "").strip()
            _chost = st.session_state.get("custom_provider_api_host", "").strip()
            _cpath = st.session_state.get("custom_provider_api_path", "").strip()
            _ccompat = st.session_state.get("custom_provider_network_compat", False)
            if not _ckey:
                st.error(t("custom_provider_api_key_missing"))
            elif not _chost:
                st.error(t("custom_provider_host_missing"))
            else:
                _proto = "http" if _ccompat else "https"
                _base_url = f"{_proto}://{_chost}{_cpath}"
                try:
                    _check_client = OpenAICompatibleClient(api_key=_ckey, base_url=_base_url)
                    _check_client.list_models()
                    st.success(t("custom_provider_key_ok"))
                except Exception as _check_err:
                    st.error(t("custom_provider_key_fail").format(str(_check_err)))

        # API host and path side by side
        col_host, col_path = st.columns(2)
        with col_host:
            st.text_input(
                t("custom_provider_api_host"),
                key="custom_provider_api_host",
                placeholder="api.openai.com",
            )
        with col_path:
            st.text_input(
                t("custom_provider_api_path"),
                key="custom_provider_api_path",
                placeholder="/v1",
            )

        # Network compatibility toggle
        st.toggle(
            t("custom_provider_network_compat"),
            key="custom_provider_network_compat",
            value=False,
        )

        # Models section
        st.markdown(f"**{t('custom_provider_models_label')}**")
        col_add_btn, col_reset_btn, col_fetch_btn = st.columns(3)
        with col_add_btn:
            open_add_model = st.button(t("custom_provider_add_model"), key="custom_provider_open_add_model", use_container_width=True)
        with col_reset_btn:
            reset_models_btn = st.button(t("custom_provider_reset_models"), key="custom_provider_reset_models_btn", use_container_width=True)
        with col_fetch_btn:
            fetch_models_btn = st.button(t("custom_provider_fetch_models"), key="custom_provider_fetch_models_btn", use_container_width=True)

        if reset_models_btn:
            st.session_state.custom_provider_models = []
            st.rerun()

        if fetch_models_btn:
            _ckey = st.session_state.get("custom_provider_api_key", "").strip()
            _chost = st.session_state.get("custom_provider_api_host", "").strip()
            _cpath = st.session_state.get("custom_provider_api_path", "").strip()
            _ccompat = st.session_state.get("custom_provider_network_compat", False)
            if not _ckey:
                st.error(t("custom_provider_api_key_missing"))
            elif not _chost:
                st.error(t("custom_provider_host_missing"))
            else:
                _proto = "http" if _ccompat else "https"
                _base_url = f"{_proto}://{_chost}{_cpath}"
                try:
                    _fetch_client = OpenAICompatibleClient(api_key=_ckey, base_url=_base_url)
                    _fetched = _fetch_client.list_models()
                    st.session_state.custom_provider_models = _fetched
                    st.success(t("custom_provider_fetch_ok").format(len(_fetched)))
                    st.rerun()
                except Exception as _fetch_err:
                    st.error(t("custom_provider_fetch_fail").format(str(_fetch_err)))

        if open_add_model:
            st.session_state.custom_provider_add_model_open = True

        if st.session_state.get("custom_provider_add_model_open"):
            new_model_name = st.text_input(
                t("custom_provider_models_label"),
                key="custom_provider_new_model_input",
                placeholder=t("custom_provider_new_model_placeholder"),
                label_visibility="collapsed",
            )
            if st.button("✅", key="custom_provider_confirm_add_model"):
                if new_model_name.strip():
                    models = st.session_state.custom_provider_models
                    if new_model_name.strip() not in models:
                        models.append(new_model_name.strip())
                        st.session_state.custom_provider_models = models
                    st.session_state.custom_provider_add_model_open = False
                    st.rerun()

        _custom_models = st.session_state.get("custom_provider_models", [])
        if _custom_models:
            selected_model = st.selectbox(
                t("ai_model"),
                options=_custom_models,
                index=0,
                key="custom_model_selector",
            )
        else:
            selected_model = st.text_input(
                t("ai_model"),
                key="custom_model_direct_input",
                placeholder=t("custom_provider_new_model_placeholder"),
            )
    else:
        openai_api_key_input = ""
        selected_model = st.selectbox(
            t("ai_model"),
            options=CEREBRAS_MODEL_OPTIONS,
            index=0,
            key="cerebras_model_selector",
            help="\n".join(f"• {k}: {v}" for k, v in CEREBRAS_MODEL_DESCRIPTIONS.items())
        )
    
    system_prompts_data = load_system_prompts()
    prompts_list = system_prompts_data.get("prompts", [])
    prompt_names = [prompt["name"] for prompt in prompts_list]
    selected_prompt = system_prompts_data.get("selected")
    
    if prompt_names:
        selected_index = 0
        if selected_prompt in prompt_names:
            selected_index = prompt_names.index(selected_prompt)
        
        selected_name = st.selectbox(
            t("select_prompt"),
            options=prompt_names,
            index=selected_index,
            key="qwen_system_prompt_selector",
            help=t("select_prompt_help")
        )
        
        system_prompts_data["selected"] = selected_name
        
        selected_content = ""
        for prompt in prompts_list:
            if prompt["name"] == selected_name:
                selected_content = prompt["content"]
                break
        
        if 'qwen_system_prompt' not in st.session_state:
            st.session_state.qwen_system_prompt = selected_content
        elif selected_name != st.session_state.get("last_selected_qwen_prompt"):
            st.session_state.qwen_system_prompt = selected_content
        
        st.session_state.last_selected_qwen_prompt = selected_name
        
        new_content = st.text_area(
            t("edit_prompt"),
            value=st.session_state.qwen_system_prompt,
            height=150,
            placeholder=t("edit_prompt_placeholder"),
            key="qwen_system_editor"
        )
        
        st.session_state.qwen_system_prompt = new_content
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("update_prompt"), key="update_qwen_prompt_button"):
                for prompt in prompts_list:
                    if prompt["name"] == selected_name:
                        prompt["content"] = new_content
                        break
                if save_system_prompts(system_prompts_data):
                    st.toast(t("prompt_updated").format(selected_name))
        
        with col2:
            if st.button(t("delete_prompt"), key="delete_qwen_prompt_button", 
                        disabled=len(prompts_list) <= 1):
                prompts_list = [p for p in prompts_list if p["name"] != selected_name]
                system_prompts_data["prompts"] = prompts_list
                if selected_name == selected_prompt and prompts_list:
                    system_prompts_data["selected"] = prompts_list[0]["name"]
                if save_system_prompts(system_prompts_data):
                    st.toast(t("prompt_deleted").format(selected_name))
                    st.rerun()
    
    if "qwen_form_key_suffix" not in st.session_state:
        st.session_state.qwen_form_key_suffix = 0
    
    name_key = f"new_qwen_prompt_name_{st.session_state.qwen_form_key_suffix}"
    content_key = f"new_qwen_prompt_content_{st.session_state.qwen_form_key_suffix}"
    
    with st.expander(t("add_prompt_expander"), expanded=False):
        new_prompt_name = st.text_input(t("new_prompt_name"), key=name_key)
        new_prompt_content = st.text_area(
            t("new_prompt_content"),
            height=100,
            placeholder=t("new_prompt_placeholder"),
            key=content_key
        )
        if st.button(t("add_prompt_btn"), key="add_qwen_prompt_button",
                    disabled=not new_prompt_name or not new_prompt_content):
            if new_prompt_name in prompt_names:
                st.error(t("prompt_exists").format(new_prompt_name))
            else:
                prompts_list.append({
                    "name": new_prompt_name,
                    "content": new_prompt_content
                })
                system_prompts_data["prompts"] = prompts_list
                if save_system_prompts(system_prompts_data):
                    st.session_state.qwen_form_key_suffix += 1
                    st.toast(t("prompt_added").format(new_prompt_name))
                    st.rerun()
    
    if st.toggle(t("advanced_settings"), key="qwen_advanced_settings_toggle"):
        st.session_state.qwen_max_tokens = st.slider(
            t("max_tokens"),
            1024, 32768,
            st.session_state.get("qwen_max_tokens", 8192),
            key="qwen_max_tokens_slider",
            help=t("max_tokens_help")
        )
        st.session_state.qwen_temperature = st.slider(
            t("temperature"),
            0.0, 1.5,
            st.session_state.get("qwen_temperature", 0.7),
            step=0.05,
            key="qwen_temperature_slider",
            help=t("temperature_help")
        )
    
    st.markdown("---")
    if st.toggle(t("debug_mode"), key="debug_mode_toggle", help=t("debug_help")):
        st.subheader(t("debug_info"))
        st.write("Session State:")
        st.json(st.session_state)

@st.cache_data
def gen_results(my, mm, md, mh, mmin, style, tn, sex_o, tc):
    """生成太乙計算結果，返回數據字典"""
    ty = kintaiyi.Taiyi(my, mm, md, mh, mmin)
    if style != 5:
        ttext = ty.pan(style, tn)
        kook = ty.kook(style, tn)
        sj_su_predict = f"始擊落{ty.sf_num(style, tn)}宿，{su_dist.get(ty.sf_num(style, tn))}"
        tg_sj_su_predict = config.multi_key_dict_get(tengan_shiji, config.gangzhi(my, mm, md, mh, mmin)[0][0]).get(config.Ganzhiwuxing(ty.sf(style, tn)))
        three_door = ty.threedoors(style, tn)
        five_generals = ty.fivegenerals(style, tn)
        home_vs_away1 = ty.wc_n_sj(style, tn)
        genchart2 = ty.gen_gong(style, tn, tc)
    if style == 5:
        tn = 0
        ttext = ty.pan(3, 0)
        kook = ty.kook(3, 0)
        sj_su_predict = f"始擊落{ty.sf_num(3, 0)}宿，{su_dist.get(ty.sf_num(3, 0))}"
        tg_sj_su_predict = config.multi_key_dict_get(tengan_shiji, config.gangzhi(my, mm, md, mh, mmin)[0][0]).get(config.Ganzhiwuxing(ty.sf(3, 0)))
        three_door = ty.threedoors(3, 0)
        five_generals = ty.fivegenerals(3, 0)
        home_vs_away1 = ty.wc_n_sj(3, 0)
        genchart2 = ty.gen_gong(3, tn, tc)
    genchart1 = ty.gen_life_gong(sex_o)
    kook_num = kook.get("數")
    yingyang = kook.get("文")[0]
    wuyuan = ty.get_five_yuan_kook(style, tn) if style != 5 else ""
    homecal, awaycal, setcal = config.find_cal(yingyang, kook_num)
    zhao = {"男": "乾造", "女": "坤造"}.get(sex_o)
    life1 = ty.gongs_discription(sex_o)
    life2 = ty.twostar_disc(sex_o)
    lifedisc = ty.convert_gongs_text(life1, life2)
    lifedisc2 = ty.stars_descriptions_text(3, 0)
    lifedisc3 = ty.sixteen_gong_grades(3,0)
    yc = ty.year_chin()
    year_predict = f"太歲{yc}值宿，{su_dist.get(yc)}"
    home_vs_away3 = ttext.get("推太乙風雲飛鳥助戰法")
    ts = taiyi_yingyang.get(kook.get('文')[0:2]).get(kook.get('數'))
    gz = f"{ttext.get('干支')[0]}年 {ttext.get('干支')[1]}月 {ttext.get('干支')[2]}日 {ttext.get('干支')[3]}時 {ttext.get('干支')[4]}分"
    lunard = f"{cn2an.transform(str(config.lunar_date_d(my, mm, md).get('年')) + '年', 'an2cn')}{an2cn(config.lunar_date_d(my, mm, md).get('月'))}月{an2cn(config.lunar_date_d(my, mm, md).get('日'))}日"
    ch = chistory.get(my, "")
    tys = "".join([ts[i:i+25] + "\n" for i in range(0, len(ts), 25)])
    yjxx = ty.yangjiu_xingxian(sex_o)
    blxx = ty.bailiu_xingxian(sex_o)
    ygua = ty.year_gua()[1]
    mgua = ty.month_gua()[1]
    dgua = ty.day_gua()[1]
    hgua = ty.hour_gua()[1]
    mingua = ty.minute_gua()[1]
    
    return {
        "ttext": ttext,
        "kook": kook,
        "sj_su_predict": sj_su_predict,
        "tg_sj_su_predict": tg_sj_su_predict,
        "three_door": three_door,
        "five_generals": five_generals,
        "home_vs_away1": home_vs_away1,
        "genchart1": genchart1,
        "genchart2": genchart2,
        "kook_num": kook_num,
        "yingyang": yingyang,
        "wuyuan": wuyuan,
        "homecal": homecal,
        "awaycal": awaycal,
        "setcal": setcal,
        "zhao": zhao,
        "life1": life1,
        "life2": life2,
        "lifedisc": lifedisc,
        "lifedisc2": lifedisc2,
        "lifedisc3": lifedisc3,
        "year_predict": year_predict,
        "home_vs_away3": home_vs_away3,
        "ts": ts,
        "gz": gz,
        "lunard": lunard,
        "ch": ch,
        "tys": tys,
        "yjxx": yjxx,
        "blxx": blxx,
        "ygua": ygua,
        "mgua": mgua,
        "dgua": dgua,
        "hgua": hgua,
        "mingua": mingua,
        "style": style,
        "tn": tn,
        "sex_o": sex_o,
        "ty": ty
    }

# 創建標籤頁
tabs = st.tabs([t('tab_chart'), t('tab_instructions'), t('tab_history'), t('tab_disaster'), t('tab_books'), t('tab_updates'), t('tab_guide'), t('tab_links')])

# 太乙排盤
with tabs[0]:
    output = st.empty()
    with st_capture(output.code):
        try:
            if instant:
                now = datetime.datetime.now(pytz.timezone('Asia/Hong_Kong'))
                results = gen_results(now.year, now.month, now.day, now.hour, now.minute, style, tn, sex_o, tc)
                st.session_state.render_default = False
            else:
                results = gen_results(my, mm, md, mh, mmin, style, tn, sex_o, tc)
                st.session_state.render_default = False

            if results:
                if results["style"] == 5:
                    try:
                        start_pt = results["genchart1"][results["genchart1"].index('''viewBox="''')+22:].split(" ")[1]
                        if rotation == "轉動":
                            render_svg(results["genchart1"], int(start_pt))
                        else:
                            render_svg1(results["genchart1"], int(start_pt))
                    except (ValueError, IndexError) as e:
                        st.error(f"Failed to parse SVG viewBox: {str(e)}")
                    with st.expander(t("explanation")):
                        st.title(t("taiyi_life_title"))
                        st.markdown(t("twelve_palaces"))
                        st.markdown(results["lifedisc"])
                        st.markdown("   ")
                        st.markdown(t("sixteen_gods"))
                        st.markdown(results["lifedisc2"])
                        st.markdown("   ")
                        st.markdown(t("sixteen_grades"))
                        st.markdown(results["lifedisc3"])
                        st.markdown("   ")
                        st.markdown(t("hexagram"))
                        st.markdown(f"{t('year_hex')}{results['ygua']}")
                        st.markdown(f"{t('month_hex')}{results['mgua']}")
                        st.markdown(f"{t('day_hex')}{results['dgua']}")
                        st.markdown(f"{t('hour_hex')}{results['hgua']}")
                        st.markdown(f"{t('minute_hex')}{results['mingua']}")
                        st.markdown("   ")
                        st.markdown(t("yang_nine"))
                        st.markdown(format_text(results["yjxx"]))
                        st.markdown("   ")
                        st.markdown(t("bai_liu"))
                        st.markdown(format_text(results["blxx"]))
                        st.markdown("   ")
                        st.title(t("taiyi_mishu"))
                        st.markdown(results["ts"])
                        st.title(t("history_records"))
                        st.markdown(results["ch"])
                    print(f"{config.gendatetime(my, mm, md, mh, mmin)} {results['zhao']} - {results['ty'].taiyi_life(results['sex_o']).get('性別')} - {config.taiyi_name(0)[0]} - {results['ty'].accnum(0, 0)} | \n{t('lunar_label')}︰{results['lunard']} | {jieqi.jq(my, mm, md, mh, mmin)} |\n{results['gz']} |\n{config.kingyear(my)} |\n{t('taiyi_life_method')} - {results['ty'].kook(0, 0).get('文')} ({results['ttext'].get('局式').get('年')}) | \n{t('epoch_label')}︰{results['ttext'].get('紀元')} | {t('home_calc')}︰{results['homecal']} {t('away_calc')}︰{results['awaycal']} |")
                else:
                    try:
                        start_pt2 = results["genchart2"][results["genchart2"].index('''viewBox="''')+22:].split(" ")[1]
                        if rotation == "轉動":
                            render_svg(results["genchart2"], int(start_pt2))
                        else:
                            render_svg1(results["genchart2"], int(start_pt2))
                    except (ValueError, IndexError) as e:
                        st.error(f"Failed to parse SVG viewBox: {str(e)}")
                    with st.expander(t("explanation")):
                        st.title(t("taiyi_mishu"))
                        st.markdown(results["ts"])
                        st.title(t("history_records"))
                        st.markdown(results["ch"])
                        st.title(t("chart_analysis"))
                        st.markdown(f"{t('year_star_predict')}{results['year_predict']}")
                        st.markdown(f"{t('start_star_predict')}{results['sj_su_predict']}")
                        st.markdown(f"{t('ten_stem_predict')}{results['tg_sj_su_predict']}")
                        st.markdown(f"{t('sky_ground_method')}{results['ty'].ty_gong_dist(results['style'], results['tn'])}")
                        st.markdown(f"{t('three_five')}{results['three_door'] + results['five_generals']}")
                        st.markdown(f"{t('home_away')}{results['home_vs_away1']}")
                        st.markdown(f"{t('win_loss')}{results['ttext'].get('推少多以占勝負')}")
                        st.markdown(f"{t('wind_cloud')}{results['home_vs_away3']}")
                        st.markdown(f"{t('solitary')}{results['ttext'].get('推孤單以占成敗')}")
                        st.markdown(f"{t('yin_yang_adversity')}{results['ttext'].get('推陰陽以占厄會')}")
                        st.markdown(f"{t('emperor_tour')}{results['ttext'].get('明天子巡狩之期術')}")
                        st.markdown(f"{t('ruler_base')}{results['ttext'].get('明君基太乙所主術')}")
                        st.markdown(f"{t('minister_base')}{results['ttext'].get('明臣基太乙所主術')}")
                        st.markdown(f"{t('people_base')}{results['ttext'].get('明民基太乙所主術')}")
                        st.markdown(f"{t('five_blessings')}{results['ttext'].get('明五福太乙所主術')}")
                        st.markdown(f"{t('five_blessings_calc')}{results['ttext'].get('明五福吉算所主術')}")
                        st.markdown(f"{t('heaven_yi')}{results['ttext'].get('明天乙太乙所主術')}")
                        st.markdown(f"{t('earth_yi')}{results['ttext'].get('明地乙太乙所主術')}")
                        st.markdown(f"{t('zhifu')}{results['ttext'].get('明值符太乙所主術')}")



                    
                    print(f"{config.gendatetime(my, mm, md, mh, mmin)} | {t('acc_prefix')}{config.taiyi_name(results['style'])[0]}{t('acc_suffix')}︰{results['ty'].accnum(results['style'], results['tn'])} | \n"
                          f"{t('lunar_label')}︰{results['lunard']} | {jieqi.jq(my, mm, md, mh, mmin)} |\n"
                          f"{results['gz']} |\n"
                          f"{config.kingyear(my)} |\n"
                          f"{config.ty_method(results['tn'])}{results['ttext'].get('太乙計', '')} - {results['ty'].kook(results['style'], results['tn']).get('文', '')} "
                          f"({results['ttext'].get('局式', {}).get('年', '')}) \n{t('five_yuan')}:{results['wuyuan']} | \n"
                          f"{t('epoch_label')}︰{results['ttext'].get('紀元', '')} | {t('home_calc')}︰{results['homecal']} {t('away_calc')}︰{results['awaycal']} {t('set_calc')}︰{results['setcal']} |")

                # ── 運籌博弈分析區塊 ──────────────────────────────────────
                if st.toggle(t("game_theory_toggle"), key="game_theory_toggle_switch"):
                    with st.spinner(t("game_theory_computing")):
                        try:
                            gt = TaiyiGame(results["ttext"])
                            gt_report = gt.分析報告()
                        except Exception as gt_err:
                            st.error(f"博弈分析錯誤：{gt_err}")
                            gt_report = None
                    if gt_report:
                        with st.expander(t("game_theory_header"), expanded=True):
                            st.markdown(f"**古法推主客相闗：** {gt_report['古法推主客相闗']}")
                            st.markdown(f"**{t('game_theory_winrate')}：** {gt_report['主方勝率判斷']}")
                            st.markdown(f"**{t('game_theory_value')}：** `{gt_report['博弈均衡值']}`")

                            st.markdown(f"##### {t('game_theory_payoff')}")
                            payoff_df = pd.DataFrame(
                                gt_report["支付矩陣"],
                                index=_gt_主方策略列,
                                columns=_gt_客方策略列,
                            ).round(2)
                            st.dataframe(payoff_df)

                            col_h, col_a = st.columns(2)
                            with col_h:
                                st.markdown(f"**{t('game_theory_home_strategy')}**")
                                home_df = pd.DataFrame(
                                    {"策略": _gt_主方策略列, "概率": gt_report["主方均衡策略"]}
                                )
                                st.dataframe(home_df, hide_index=True)
                            with col_a:
                                st.markdown(f"**{t('game_theory_away_strategy')}**")
                                away_df = pd.DataFrame(
                                    {"策略": _gt_客方策略列, "概率": gt_report["客方均衡策略"]}
                                )
                                st.dataframe(away_df, hide_index=True)

                            lp = gt_report["LP最大勝率"]
                            st.markdown(f"##### {t('game_theory_lp')}")
                            st.info(lp["建議文字"])
                            st.markdown(f"**主方最優純策略：** {gt_report['主方最優純策略']}")
                            st.markdown(f"**客方最優純策略：** {gt_report['客方最優純策略']}")

                if st.button(t("ai_analyze_btn"), key="analyze_with_qwen"):
                    with st.spinner(t("ai_analyzing")):
                        _provider = st.session_state.get("ai_provider_selector", "Cerebras")
                        if _provider == "OpenAI":
                            _openai_key = st.session_state.get("openai_api_key_input", "").strip()
                            if not _openai_key:
                                st.error(t("openai_api_key_missing"))
                            else:
                                try:
                                    client = OpenAIClient(api_key=_openai_key)
                                    taiyi_prompt = format_taiyi_results_for_prompt(results)
                                    if st.session_state.get("game_theory_toggle_switch"):
                                        try:
                                            gt_summary = TaiyiGame(results["ttext"]).格局摘要文字()
                                            taiyi_prompt = taiyi_prompt + "\n\n" + gt_summary
                                        except Exception as gt_err:
                                            st.warning(f"博弈摘要生成失敗（不影響AI分析）：{gt_err}")
                                    messages = [
                                        {"role": "system", "content": st.session_state.qwen_system_prompt},
                                        {"role": "user", "content": taiyi_prompt}
                                    ]
                                    api_params = {
                                        "messages": messages,
                                        "model": selected_model,
                                        "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                                        "temperature": st.session_state.get("qwen_temperature", 0.7)
                                    }
                                    response = client.get_chat_completion(**api_params)
                                    raw_response = response.choices[0].message.content
                                    with st.expander(t("ai_result"), expanded=True):
                                        st.markdown(raw_response)
                                except OpenAITokenQuotaExceededError:
                                    st.error(t("ai_openai_quota_exceeded"))
                                except Exception as e:
                                    st.error(t("ai_error").format(str(e)))
                        elif _provider == "xAI (Grok)":
                            _xai_key = st.session_state.get("xai_api_key_input", "").strip()
                            if not _xai_key:
                                st.error(t("xai_api_key_missing"))
                            else:
                                try:
                                    client = OpenAICompatibleClient(api_key=_xai_key, base_url=XAI_BASE_URL)
                                    taiyi_prompt = format_taiyi_results_for_prompt(results)
                                    if st.session_state.get("game_theory_toggle_switch"):
                                        try:
                                            gt_summary = TaiyiGame(results["ttext"]).格局摘要文字()
                                            taiyi_prompt = taiyi_prompt + "\n\n" + gt_summary
                                        except Exception as gt_err:
                                            st.warning(f"博弈摘要生成失敗（不影響AI分析）：{gt_err}")
                                    messages = [
                                        {"role": "system", "content": st.session_state.qwen_system_prompt},
                                        {"role": "user", "content": taiyi_prompt}
                                    ]
                                    api_params = {
                                        "messages": messages,
                                        "model": selected_model,
                                        "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                                        "temperature": st.session_state.get("qwen_temperature", 0.7)
                                    }
                                    response = client.get_chat_completion(**api_params)
                                    raw_response = response.choices[0].message.content
                                    with st.expander(t("ai_result"), expanded=True):
                                        st.markdown(raw_response)
                                except CompatibleTokenQuotaExceededError:
                                    st.error(t("ai_xai_quota_exceeded"))
                                except Exception as e:
                                    st.error(t("ai_error").format(str(e)))
                        elif _provider == "DeepSeek":
                            _deepseek_key = st.session_state.get("deepseek_api_key_input", "").strip()
                            if not _deepseek_key:
                                st.error(t("deepseek_api_key_missing"))
                            else:
                                try:
                                    client = OpenAICompatibleClient(api_key=_deepseek_key, base_url=DEEPSEEK_BASE_URL)
                                    taiyi_prompt = format_taiyi_results_for_prompt(results)
                                    if st.session_state.get("game_theory_toggle_switch"):
                                        try:
                                            gt_summary = TaiyiGame(results["ttext"]).格局摘要文字()
                                            taiyi_prompt = taiyi_prompt + "\n\n" + gt_summary
                                        except Exception as gt_err:
                                            st.warning(f"博弈摘要生成失敗（不影響AI分析）：{gt_err}")
                                    messages = [
                                        {"role": "system", "content": st.session_state.qwen_system_prompt},
                                        {"role": "user", "content": taiyi_prompt}
                                    ]
                                    api_params = {
                                        "messages": messages,
                                        "model": selected_model,
                                        "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                                        "temperature": st.session_state.get("qwen_temperature", 0.7)
                                    }
                                    response = client.get_chat_completion(**api_params)
                                    raw_response = response.choices[0].message.content
                                    with st.expander(t("ai_result"), expanded=True):
                                        st.markdown(raw_response)
                                except CompatibleTokenQuotaExceededError:
                                    st.error(t("ai_deepseek_quota_exceeded"))
                                except Exception as e:
                                    st.error(t("ai_error").format(str(e)))
                        elif _provider == "Qwen":
                            _qwen_key = st.session_state.get("qwen_api_key_input", "").strip()
                            if not _qwen_key:
                                st.error(t("qwen_api_key_missing"))
                            else:
                                try:
                                    client = OpenAICompatibleClient(api_key=_qwen_key, base_url=QWEN_BASE_URL)
                                    taiyi_prompt = format_taiyi_results_for_prompt(results)
                                    if st.session_state.get("game_theory_toggle_switch"):
                                        try:
                                            gt_summary = TaiyiGame(results["ttext"]).格局摘要文字()
                                            taiyi_prompt = taiyi_prompt + "\n\n" + gt_summary
                                        except Exception as gt_err:
                                            st.warning(f"博弈摘要生成失敗（不影響AI分析）：{gt_err}")
                                    messages = [
                                        {"role": "system", "content": st.session_state.qwen_system_prompt},
                                        {"role": "user", "content": taiyi_prompt}
                                    ]
                                    api_params = {
                                        "messages": messages,
                                        "model": selected_model,
                                        "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                                        "temperature": st.session_state.get("qwen_temperature", 0.7)
                                    }
                                    response = client.get_chat_completion(**api_params)
                                    raw_response = response.choices[0].message.content
                                    with st.expander(t("ai_result"), expanded=True):
                                        st.markdown(raw_response)
                                except CompatibleTokenQuotaExceededError:
                                    st.error(t("ai_qwen_quota_exceeded"))
                                except Exception as e:
                                    st.error(t("ai_error").format(str(e)))
                        elif _provider == "사용자 정의":
                            _ckey = st.session_state.get("custom_provider_api_key", "").strip()
                            _chost = st.session_state.get("custom_provider_api_host", "").strip()
                            _cpath = st.session_state.get("custom_provider_api_path", "").strip()
                            _ccompat = st.session_state.get("custom_provider_network_compat", False)
                            _cmodel = st.session_state.get("custom_model_selector") or st.session_state.get("custom_model_direct_input", "") or selected_model
                            if not _ckey:
                                st.error(t("custom_provider_api_key_missing"))
                            elif not _chost:
                                st.error(t("custom_provider_host_missing"))
                            elif not _cmodel:
                                st.error(t("custom_provider_no_models"))
                            else:
                                _proto = "http" if _ccompat else "https"
                                _base_url = f"{_proto}://{_chost}{_cpath}"
                                try:
                                    client = OpenAICompatibleClient(api_key=_ckey, base_url=_base_url)
                                    taiyi_prompt = format_taiyi_results_for_prompt(results)
                                    if st.session_state.get("game_theory_toggle_switch"):
                                        try:
                                            gt_summary = TaiyiGame(results["ttext"]).格局摘要文字()
                                            taiyi_prompt = taiyi_prompt + "\n\n" + gt_summary
                                        except Exception as gt_err:
                                            st.warning(f"博弈摘要生成失敗（不影響AI分析）：{gt_err}")
                                    messages = [
                                        {"role": "system", "content": st.session_state.qwen_system_prompt},
                                        {"role": "user", "content": taiyi_prompt}
                                    ]
                                    api_params = {
                                        "messages": messages,
                                        "model": _cmodel,
                                        "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                                        "temperature": st.session_state.get("qwen_temperature", 0.7)
                                    }
                                    response = client.get_chat_completion(**api_params)
                                    raw_response = response.choices[0].message.content
                                    with st.expander(t("ai_result"), expanded=True):
                                        st.markdown(raw_response)
                                except CompatibleTokenQuotaExceededError:
                                    st.error(t("ai_custom_quota_exceeded"))
                                except Exception as e:
                                    st.error(t("ai_error").format(str(e)))
                        else:
                            cerebras_api_key = st.secrets.get("CEREBRAS_API_KEY") or os.getenv("CEREBRAS_API_KEY")
                            if not cerebras_api_key:
                                st.error(t("ai_key_missing"))
                            else:
                                try:
                                    client = CerebrasClient(api_key=cerebras_api_key)
                                    taiyi_prompt = format_taiyi_results_for_prompt(results)
                                    # 若博弈分析已啟用，附加博弈摘要到提示詞
                                    if st.session_state.get("game_theory_toggle_switch"):
                                        try:
                                            gt_summary = TaiyiGame(results["ttext"]).格局摘要文字()
                                            taiyi_prompt = taiyi_prompt + "\n\n" + gt_summary
                                        except Exception as gt_err:
                                            st.warning(f"博弈摘要生成失敗（不影響AI分析）：{gt_err}")
                                    messages = [
                                        {"role": "system", "content": st.session_state.qwen_system_prompt},
                                        {"role": "user", "content": taiyi_prompt}
                                    ]
                                    api_params = {
                                        "messages": messages,
                                        "model": selected_model,
                                        "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                                        "temperature": st.session_state.get("qwen_temperature", 0.7)
                                    }
                                    response = client.get_chat_completion(**api_params)
                                    raw_response = response.choices[0].message.content
                                    with st.expander(t("ai_result"), expanded=True):
                                        st.markdown(raw_response)
                                except TokenQuotaExceededError:
                                    st.error(t("ai_quota_exceeded"))
                                except Exception as e:
                                    st.error(t("ai_error").format(str(e)))
        except Exception as e:
            st.error(t("gen_error").format(str(e)))

# 使用說明
with tabs[1]:
    st.markdown(get_file_content_as_string(BASE_URL_KINTAIYI, "docs/instruction.md"))

# 太乙局數史例
with tabs[2]:
    with open(os.path.join(_REPO_ROOT, "assets", "example.json"), "r") as f:
        data = f.read()
    timeline(data, height=600)
    with st.expander(t("list_label")):
        st.markdown(get_file_content_as_string(BASE_URL_KINTAIYI, "docs/example.md"))

# 災害統計
with tabs[3]:
    st.markdown(get_file_content_as_string(BASE_URL_KINTAIYI, "docs/disaster.md"))

# 古籍書目
with tabs[4]:
    st.markdown(get_file_content_as_string(BASE_URL_KINTAIYI, "docs/guji.md"))

# 更新日誌
with tabs[5]:
    _update_md = get_file_content_as_string(BASE_URL_KINTAIYI, "docs/update.md")
    st.markdown(render_changelog_html(_update_md), unsafe_allow_html=True)

# 看盤要領
with tabs[6]:
    st.markdown(get_file_content_as_string(BASE_URL_KINTAIYI, "docs/tutorial.md"), unsafe_allow_html=True)

# 連結
with tabs[7]:
    st.markdown(get_file_content_as_string(BASE_URL_KINLIUREN, "docs/contact.md"), unsafe_allow_html=True)

# Note: global styling is now handled by custom_css.py (injected near the top of this file).

# ── Fixed Bottom LLM Chat Section ───────────────────────────────────────
# Initialize chat history in session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

st.markdown("---")
st.markdown(f"### {t('chat_header')}")

# Clear chat button
if st.button(t("chat_clear"), key="clear_chat_btn"):
    st.session_state.chat_messages = []
    st.rerun()

# Display welcome message if no messages yet
if not st.session_state.chat_messages:
    with st.chat_message("assistant", avatar="👲"):
        st.markdown(t("chat_welcome"))

# Display chat history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"], avatar="👲" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

# Chat input (Streamlit auto-fixes this at the bottom)
if user_input := st.chat_input(t("chat_placeholder")):
    # Add user message to history
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response
    with st.chat_message("assistant", avatar="👲"):
        _provider = st.session_state.get("ai_provider_selector", "Cerebras")
        if _provider == "OpenAI":
            _openai_key = st.session_state.get("openai_api_key_input", "").strip()
            if not _openai_key:
                error_msg = t("openai_api_key_missing")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            else:
                with st.spinner(t("chat_thinking")):
                    try:
                        client = OpenAIClient(api_key=_openai_key)
                        _default_prompt = t("chat_welcome")
                        system_prompt = st.session_state.get("qwen_system_prompt", _default_prompt)
                        messages = [{"role": "system", "content": system_prompt}]
                        messages.extend(st.session_state.chat_messages[-_MAX_CHAT_HISTORY:])
                        api_params = {
                            "messages": messages,
                            "model": st.session_state.get("openai_model_selector", OPENAI_MODEL_OPTIONS[0]),
                            "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                            "temperature": st.session_state.get("qwen_temperature", 0.7),
                        }
                        response = client.get_chat_completion(**api_params)
                        reply = response.choices[0].message.content
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except OpenAITokenQuotaExceededError:
                        error_msg = t("ai_openai_quota_exceeded")
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = t("ai_error").format(str(e))
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
        elif _provider == "xAI (Grok)":
            _xai_key = st.session_state.get("xai_api_key_input", "").strip()
            if not _xai_key:
                error_msg = t("xai_api_key_missing")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            else:
                with st.spinner(t("chat_thinking")):
                    try:
                        client = OpenAICompatibleClient(api_key=_xai_key, base_url=XAI_BASE_URL)
                        _default_prompt = t("chat_welcome")
                        system_prompt = st.session_state.get("qwen_system_prompt", _default_prompt)
                        messages = [{"role": "system", "content": system_prompt}]
                        messages.extend(st.session_state.chat_messages[-_MAX_CHAT_HISTORY:])
                        api_params = {
                            "messages": messages,
                            "model": st.session_state.get("xai_model_selector", XAI_MODEL_OPTIONS[0]),
                            "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                            "temperature": st.session_state.get("qwen_temperature", 0.7),
                        }
                        response = client.get_chat_completion(**api_params)
                        reply = response.choices[0].message.content
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except CompatibleTokenQuotaExceededError:
                        error_msg = t("ai_xai_quota_exceeded")
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = t("ai_error").format(str(e))
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
        elif _provider == "DeepSeek":
            _deepseek_key = st.session_state.get("deepseek_api_key_input", "").strip()
            if not _deepseek_key:
                error_msg = t("deepseek_api_key_missing")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            else:
                with st.spinner(t("chat_thinking")):
                    try:
                        client = OpenAICompatibleClient(api_key=_deepseek_key, base_url=DEEPSEEK_BASE_URL)
                        _default_prompt = t("chat_welcome")
                        system_prompt = st.session_state.get("qwen_system_prompt", _default_prompt)
                        messages = [{"role": "system", "content": system_prompt}]
                        messages.extend(st.session_state.chat_messages[-_MAX_CHAT_HISTORY:])
                        api_params = {
                            "messages": messages,
                            "model": st.session_state.get("deepseek_model_selector", DEEPSEEK_MODEL_OPTIONS[0]),
                            "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                            "temperature": st.session_state.get("qwen_temperature", 0.7),
                        }
                        response = client.get_chat_completion(**api_params)
                        reply = response.choices[0].message.content
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except CompatibleTokenQuotaExceededError:
                        error_msg = t("ai_deepseek_quota_exceeded")
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = t("ai_error").format(str(e))
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
        elif _provider == "Qwen":
            _qwen_key = st.session_state.get("qwen_api_key_input", "").strip()
            if not _qwen_key:
                error_msg = t("qwen_api_key_missing")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            else:
                with st.spinner(t("chat_thinking")):
                    try:
                        client = OpenAICompatibleClient(api_key=_qwen_key, base_url=QWEN_BASE_URL)
                        _default_prompt = t("chat_welcome")
                        system_prompt = st.session_state.get("qwen_system_prompt", _default_prompt)
                        messages = [{"role": "system", "content": system_prompt}]
                        messages.extend(st.session_state.chat_messages[-_MAX_CHAT_HISTORY:])
                        api_params = {
                            "messages": messages,
                            "model": st.session_state.get("qwen_model_selector", QWEN_MODEL_OPTIONS[0]),
                            "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                            "temperature": st.session_state.get("qwen_temperature", 0.7),
                        }
                        response = client.get_chat_completion(**api_params)
                        reply = response.choices[0].message.content
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except CompatibleTokenQuotaExceededError:
                        error_msg = t("ai_qwen_quota_exceeded")
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = t("ai_error").format(str(e))
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
        elif _provider == "사용자 정의":
            _ckey = st.session_state.get("custom_provider_api_key", "").strip()
            _chost = st.session_state.get("custom_provider_api_host", "").strip()
            _cpath = st.session_state.get("custom_provider_api_path", "").strip()
            _ccompat = st.session_state.get("custom_provider_network_compat", False)
            _cmodel = st.session_state.get("custom_model_selector") or st.session_state.get("custom_model_direct_input", "")
            if not _ckey:
                error_msg = t("custom_provider_api_key_missing")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            elif not _chost:
                error_msg = t("custom_provider_host_missing")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            elif not _cmodel:
                error_msg = t("custom_provider_no_models")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            else:
                _proto = "http" if _ccompat else "https"
                _base_url = f"{_proto}://{_chost}{_cpath}"
                with st.spinner(t("chat_thinking")):
                    try:
                        client = OpenAICompatibleClient(api_key=_ckey, base_url=_base_url)
                        _default_prompt = t("chat_welcome")
                        system_prompt = st.session_state.get("qwen_system_prompt", _default_prompt)
                        messages = [{"role": "system", "content": system_prompt}]
                        messages.extend(st.session_state.chat_messages[-_MAX_CHAT_HISTORY:])
                        api_params = {
                            "messages": messages,
                            "model": _cmodel,
                            "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                            "temperature": st.session_state.get("qwen_temperature", 0.7),
                        }
                        response = client.get_chat_completion(**api_params)
                        reply = response.choices[0].message.content
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except CompatibleTokenQuotaExceededError:
                        error_msg = t("ai_custom_quota_exceeded")
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = t("ai_error").format(str(e))
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
        else:
            cerebras_api_key = st.secrets.get("CEREBRAS_API_KEY") or os.getenv("CEREBRAS_API_KEY")
            if not cerebras_api_key:
                error_msg = t("ai_key_missing")
                st.error(error_msg)
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            else:
                with st.spinner(t("chat_thinking")):
                    try:
                        client = CerebrasClient(api_key=cerebras_api_key)
                        _default_prompt = t("chat_welcome")
                        system_prompt = st.session_state.get("qwen_system_prompt", _default_prompt)
                        messages = [{"role": "system", "content": system_prompt}]
                        # Include recent chat history for context
                        messages.extend(st.session_state.chat_messages[-_MAX_CHAT_HISTORY:])
                        api_params = {
                            "messages": messages,
                            "model": st.session_state.get("cerebras_model_selector", CEREBRAS_MODEL_OPTIONS[0]),
                            "max_tokens": st.session_state.get("qwen_max_tokens", 8192),
                            "temperature": st.session_state.get("qwen_temperature", 0.7),
                        }
                        response = client.get_chat_completion(**api_params)
                        reply = response.choices[0].message.content
                        st.markdown(reply)
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except TokenQuotaExceededError:
                        error_msg = t("ai_quota_exceeded")
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = t("ai_error").format(str(e))
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
