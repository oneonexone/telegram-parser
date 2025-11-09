import asyncio
import re
import time
from telethon import TelegramClient
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Chat, Channel
from typing import List, Set, Dict
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import quote_plus, urljoin, unquote


class WebSearcher:
    def __init__(self, google_api_key: str = None, google_search_engine_id: str = None, debug=False):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru,en;q=0.9',
        })
        self.debug = debug
        self.google_api_key = google_api_key
        self.google_search_engine_id = google_search_engine_id
    
    def search_google_api(self, keyword: str, api_key: str, search_engine_id: str, max_results: int = 50) -> List[Dict]:
        print(f"🔍 Поиск через Google API: site:t.me {keyword}")
        results = []
        
        if not api_key or not search_engine_id:
            print(f"   ⚠️ Google API ключ или Search Engine ID не указаны, пропускаем")
            return results
        
        try:
            num_queries = min(10, (max_results + 9) // 10)
            print(f"   Запрашиваем {num_queries} страниц по 10 результатов...")
            
            for query_num in range(num_queries):
                start_index = query_num * 10 + 1
                query = f"site:t.me {keyword}"
                url = f"https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': api_key,
                    'cx': search_engine_id,
                    'q': query,
                    'start': start_index,
                    'num': 10
                }
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'items' in data:
                        page_count = 0
                        for item in data['items']:
                            link = item.get('link', '')
                            if 't.me/' in link:
                                username_match = re.search(r't\.me/([a-zA-Z0-9_]+)', link)
                                if username_match:
                                    username = username_match.group(1)
                        if username.lower() not in ['joinchat', 'addstickers', 's', 'c']:
                            results.append({
                                'username': username,
                                'link': f"https://t.me/{username}",
                                            'source': 'google_api'
                                        })
                                        page_count += 1
                        print(f"   Страница {query_num + 1}/10: найдено {page_count} чатов (всего: {len(results)})")
                    else:
                        print(f"   Страница {query_num + 1}/10: нет больше результатов")
                        break
                elif response.status_code == 429:
                    print(f"   ⚠️ Превышен лимит запросов Google API (100 запросов/день)")
                    break
                else:
                    print(f"   ⚠️ Ошибка Google API: {response.status_code}")
                    break
                
                if query_num < num_queries - 1:
                    time.sleep(0.5)
            
            unique_results = []
            seen_usernames = set()
            for result in results:
                if result['username'] not in seen_usernames:
                    seen_usernames.add(result['username'])
                    unique_results.append(result)
            
            print(f"   Найдено через Google API: {len(unique_results)} результатов")
            
        except Exception as e:
            print(f"   ⚠️ Ошибка поиска через Google API: {e}")
        
        return unique_results
    
    def search_duckduckgo(self, keyword: str, max_results: int = 50) -> List[Dict]:
        print(f"🦆 Поиск через DuckDuckGo: site:t.me {keyword}")
        results = []
        
        try:
            query = f"site:t.me {keyword}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            
            pages_to_fetch = min(3, max_results // 30 + 1)
            
            for page in range(pages_to_fetch):
                try:
                    if page == 0:
                        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                    else:
                        offset = page * 30
                        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&s={offset}"
                    
                    response = self.session.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    
                    if self.debug and page == 0:
                        with open(f'debug_duckduckgo_{keyword}.html', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_results_count = 0
                    
                    for result_link in soup.find_all('a', class_='result__url'):
                        text = result_link.get_text(strip=True)
                        if 't.me/' in text:
                            username_match = re.search(r't\.me/([a-zA-Z0-9_]+)', text)
                            if username_match:
                                username = username_match.group(1)
                                if username.lower() not in ['joinchat', 'addstickers', 's', 'c']:
                                    results.append({
                                        'username': username,
                                        'link': f"https://t.me/{username}",
                                        'source': 'duckduckgo'
                                    })
                                    page_results_count += 1
                    
                    for link in soup.find_all('a', class_='result__a'):
                        href = link.get('href', '')
                        if 't.me/' in href:
                            username_match = re.search(r't\.me/([a-zA-Z0-9_]+)', href)
                            if username_match:
                                username = username_match.group(1)
                                if username.lower() not in ['joinchat', 'addstickers', 's', 'c']:
                                    results.append({
                                        'username': username,
                                        'link': f"https://t.me/{username}",
                                        'source': 'duckduckgo'
                                    })
                                    page_results_count += 1
                    
            for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text(strip=True)
                        
                        for source in [href, text]:
                            if 't.me/' in source:
                                username_match = re.search(r't\.me/([a-zA-Z0-9_]+)', source)
                                if username_match:
                                    username = username_match.group(1)
                        if username.lower() not in ['joinchat', 'addstickers', 's', 'c']:
                            results.append({
                                'username': username,
                                'link': f"https://t.me/{username}",
                                            'source': 'duckduckgo'
                                        })
                                        page_results_count += 1
                    
                    if page_results_count == 0 and page > 0:
                        break
                    
                    if page < pages_to_fetch - 1:
                        time.sleep(1)
                        
                except Exception as e:
                    if page == 0:
                        raise
                    break
            
            unique_results = []
            seen_usernames = set()
            for result in results:
                if result['username'] not in seen_usernames:
                    seen_usernames.add(result['username'])
                    unique_results.append(result)
            
            print(f"   Найдено через DuckDuckGo: {len(unique_results)} результатов")
            
        except Exception as e:
            print(f"   ⚠️ Ошибка поиска через DuckDuckGo: {e}")
        
        return unique_results
    
    def get_chat_preview(self, username: str) -> Dict:
        try:
            url = f"https://t.me/{username}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            title = None
            description = None
            members = None
            
            title_tag = soup.find('meta', property='og:title')
            if title_tag:
                title = title_tag.get('content', '')
            
            if not title:
                title_tag = soup.find('div', class_='tgme_page_title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
            
            desc_tag = soup.find('meta', property='og:description')
            if desc_tag:
                description = desc_tag.get('content', '')
            
            if not description:
                desc_tag = soup.find('div', class_='tgme_page_description')
                if desc_tag:
                    description = desc_tag.get_text(strip=True)
            
            extra_tag = soup.find('div', class_='tgme_page_extra')
            if extra_tag:
                extra_text = extra_tag.get_text(strip=True)
                numbers = re.findall(r'(\d[\d\s]*)', extra_text)
                if numbers:
                    members = numbers[0].replace(' ', '')
            
            return {
                'title': title or username,
                'description': description or '',
                'members': members,
                'username': username,
                'link': url,
            }
            
        except Exception as e:
            return {
                'title': username,
                'description': '',
                'members': None,
                'username': username,
                'link': f"https://t.me/{username}",
            }


class TelegramChatParser:
    def __init__(self, api_id: int, api_hash: str, phone: str, 
                 google_api_key: str = None, google_search_engine_id: str = None,
                 debug: bool = False):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        self.debug = debug
        self.web_searcher = WebSearcher(
            google_api_key=google_api_key,
            google_search_engine_id=google_search_engine_id,
            debug=debug
        )
        
    async def connect(self):
        self.client = TelegramClient('session_' + self.phone, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        print("✅ Успешно подключено к Telegram API!")
        
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            print("🔌 Отключено от Telegram")
    
    def generate_search_variants(self, keyword: str) -> Set[str]:
        keyword_lower = keyword.lower()
        variants = {keyword_lower}
        
        variations_dict = {
            'крипт': ['крипт', 'крипта', 'крипто', 'криптовалют', 'crypto', 'bitcoin', 'btc', 'eth', 'ethereum', 'блокчейн', 'blockchain', 'token', 'coin', 'altcoin', 'defi', 'nft', 'binance', 'coinbase'],
            'crypto': ['crypto', 'bitcoin', 'btc', 'ethereum', 'eth', 'blockchain', 'cryptocurrency', 'altcoin', 'token', 'coin', 'defi', 'nft', 'web3', 'doge', 'usdt', 'trading', 'binance', 'coinbase', 'крипто', 'криптовалют'],
            'услуг': ['услуг', 'услуга', 'сервис', 'service', 'услуги'],
            'работ': ['работ', 'работа', 'вакансия', 'вакансии', 'job', 'работы'],
            'курс': ['курс', 'курсы', 'обучение', 'учеба', 'course', 'обуч'],
            'продаж': ['продаж', 'продажа', 'sell', 'sale', 'продам'],
            'покупк': ['покупк', 'покупка', 'buy', 'shopping', 'куплю'],
            'бизнес': ['бизнес', 'business', 'предприниматель', 'бизнеса'],
            'инвест': ['инвест', 'инвестиц', 'investment', 'вклад', 'инвестиции'],
            'торговл': ['торговл', 'торговля', 'трейд', 'trade', 'trading'],
            'заработ': ['заработ', 'заработок', 'доход', 'income', 'деньги', 'money'],
        }
        
        for base, variations in variations_dict.items():
            if base in keyword_lower:
                variants.update(variations)
        
        return variants
    
    def match_keyword(self, text: str, keyword: str) -> bool:
        if not text:
            return False
            
        text_lower = text.lower()
        variants = self.generate_search_variants(keyword)
        
        for variant in variants:
            if variant in text_lower:
                return True
        
        return False
    
    async def search_web(self, keyword: str) -> List[dict]:
        print(f"\n🌐 Веб-поиск чатов по запросу: '{keyword}'")
        all_web_results = []
        
        duckduckgo_results = self.web_searcher.search_duckduckgo(keyword, max_results=100)
        all_web_results.extend(duckduckgo_results)
        
        time.sleep(1)
        
        if self.web_searcher.google_api_key and self.web_searcher.google_search_engine_id:
            google_results = self.web_searcher.search_google_api(
                keyword, 
                self.web_searcher.google_api_key,
                self.web_searcher.google_search_engine_id,
                max_results=100
            )
        all_web_results.extend(google_results)
        
        seen_usernames = set()
        unique_results = []
        for result in all_web_results:
            username = result['username']
            if username not in seen_usernames:
                seen_usernames.add(username)
                unique_results.append(result)
        
        if len(unique_results) == 0:
            print(f"\n   ❌ Веб-поиск не дал результатов")
            return []
        
        print(f"\n📋 Получение подробной информации о {len(unique_results)} чатах...")
        
        detailed_results = []
        for i, result in enumerate(unique_results, 1):
            try:
                print(f"   [{i}/{len(unique_results)}] Загрузка @{result['username']}...", end='\r')
                
                preview = self.web_searcher.get_chat_preview(result['username'])
                
                if (self.match_keyword(preview['title'], keyword) or 
                    self.match_keyword(preview['description'], keyword)):
                    
                    detailed_results.append({
                        'title': preview['title'],
                        'username': result['username'],
                        'link': result['link'],
                        'id': None,
                        'about': preview['description'],
                        'members_count': preview['members'],
                        'match_in_title': self.match_keyword(preview['title'], keyword),
                        'match_in_about': self.match_keyword(preview['description'], keyword),
                        'is_channel': None,
                        'source': f"web ({result['source']})"
                    })
                
                time.sleep(0.3)
                
            except Exception as e:
                continue
        
        print(f"\n   ✅ Обработано {len(detailed_results)} релевантных чатов")
        
        return detailed_results
    
    async def search_chats_global(self, keyword: str, limit: int = 200) -> List[dict]:
        print(f"\n🔍 Поиск через Telegram API по запросу: '{keyword}'")
        results = []
        
        all_variants = list(self.generate_search_variants(keyword))
        search_variants = all_variants[:20]
        
        print(f"   Будет выполнено {len(search_variants)} запросов для максимального охвата")
        
        for i, variant in enumerate(search_variants, 1):
            try:
                print(f"   [{i}/{len(search_variants)}] Поиск: '{variant}'", end='')
                
                search_result = await self.client(SearchRequest(
                    q=variant,
                    limit=limit
                ))
                
                variant_count = 0
                for chat in search_result.chats:
                    if isinstance(chat, (Chat, Channel)):
                        chat_info = await self.extract_chat_info(chat, keyword)
                        if chat_info:
                            results.append(chat_info)
                            variant_count += 1
                
                print(f" → найдено {variant_count} чатов")
                
                await asyncio.sleep(1)
                        
            except Exception as e:
                print(f" → ошибка: {e}")
        
        seen_ids = set()
        unique_results = []
        for result in results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
        
        print(f"   Найдено через API: {len(unique_results)} уникальных чатов")
        return unique_results
    
    async def extract_chat_info(self, chat, keyword: str) -> dict:
        try:
            title = getattr(chat, 'title', 'Без названия')
            username = getattr(chat, 'username', None)
            chat_id = getattr(chat, 'id', None)
            
            about = ''
            members_count = 0
            try:
                full_chat = await self.client.get_entity(chat_id)
                if hasattr(full_chat, 'full_chat'):
                    about = getattr(full_chat.full_chat, 'about', '')
                    members_count = getattr(full_chat.full_chat, 'participants_count', 0)
            except:
                pass
            
            link = f"https://t.me/{username}" if username else f"ID: {chat_id}"
            
            match_in_title = self.match_keyword(title, keyword)
            match_in_about = self.match_keyword(about, keyword)
            
            return {
                'title': title,
                'username': username,
                'link': link,
                'id': chat_id,
                'about': about,
                'members_count': members_count,
                'match_in_title': match_in_title,
                'match_in_about': match_in_about,
                'is_channel': isinstance(chat, Channel),
                'source': 'api'
            }
        
        except Exception as e:
            return None
    
    def print_results(self, results: List[dict], keyword: str):
        if not results:
            print(f"\n❌ По запросу '{keyword}' ничего не найдено")
            return
        
        print(f"\n✅ Найдено {len(results)} чат(ов) по запросу '{keyword}':\n")
        print("=" * 80)
        
        for i, chat in enumerate(results, 1):
            print(f"\n{i}. {chat['title']}")
            
            if chat.get('is_channel') is not None:
                print(f"   Тип: {'Канал' if chat['is_channel'] else 'Группа'}")
            
            print(f"   Ссылка: {chat['link']}")
            
            if chat.get('members_count'):
                members = chat['members_count']
                if isinstance(members, int):
                    print(f"   Участников: {members:,}")
                else:
                    print(f"   Участников: {members}")
            
            if chat.get('about'):
                about = chat['about'][:200] + '...' if len(chat['about']) > 200 else chat['about']
                print(f"   Описание: {about}")
            
            match_places = []
            if chat.get('match_in_title'):
                match_places.append('в названии')
            if chat.get('match_in_about'):
                match_places.append('в описании')
            
            if match_places:
                print(f"   ✓ Найдено: {', '.join(match_places)}")
            
            source = chat.get('source', 'unknown')
            source_emoji = '🌐' if 'web' in source else '🔗'
            print(f"   {source_emoji} Источник: {source}")
            
            print("-" * 80)
    
    def save_results(self, results: List[dict], keyword: str, filename: str = None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_results_{keyword}_{timestamp}.json"
        
        data = {
            'keyword': keyword,
            'search_date': datetime.now().isoformat(),
            'total_results': len(results),
            'results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в файл: {filename}")


async def main():
    print("=" * 80)
    print("🔍 TELEGRAM CHAT PARSER v2.2 - Поиск чатов по ключевым словам")
    print("=" * 80)
    
    try:
        import config
        api_id = config.API_ID
        api_hash = config.API_HASH
        phone = config.PHONE
        google_api_key = getattr(config, 'GOOGLE_API_KEY', None)
        google_search_engine_id = getattr(config, 'GOOGLE_SEARCH_ENGINE_ID', None)
    except ImportError:
        print("\n⚠️ Файл config.py не найден!")
        print("Создайте файл config.py с вашими данными")
        print("\nВведите данные вручную:")
        api_id = int(input("API_ID: "))
        api_hash = input("API_HASH: ")
        phone = input("Номер телефона (например, +79991234567): ")
        google_api_key = None
        google_search_engine_id = None
    
    debug_choice = input("\n🔍 Включить режим отладки? (y/n): ").strip().lower()
    debug_mode = debug_choice in ['y', 'yes', 'да', 'д']
    
    if debug_mode:
        print("✅ Режим отладки включён")
    
    parser = TelegramChatParser(
        api_id, api_hash, phone,
        google_api_key=google_api_key,
        google_search_engine_id=google_search_engine_id,
        debug=debug_mode
    )
    
    try:
        await parser.connect()
        
        while True:
            print("\n" + "=" * 80)
            keyword = input("\nВведите ключевое слово для поиска (или 'exit' для выхода): ").strip()
            
            if keyword.lower() in ['exit', 'quit', 'выход']:
                print("👋 До свидания!")
                break
            
            if not keyword:
                print("⚠️ Ключевое слово не может быть пустым!")
                continue
            
            print("\nВыберите тип поиска:")
            print("1. Telegram API поиск")
            print("2. Веб-поиск (DuckDuckGo + Google API)")
            print("3. Все методы сразу (рекомендуется)")
            
            choice = input("Ваш выбор (1/2/3): ").strip()
            
            all_results = []
            
            if choice in ['1', '3']:
                results = await parser.search_chats_global(keyword)
                all_results.extend(results)
            
            if choice in ['2', '3']:
                results = await parser.search_web(keyword)
                all_results.extend(results)
            
            unique_results = []
            seen_identifiers = set()
            for result in all_results:
                identifier = result.get('username') or result.get('id')
                if identifier and identifier not in seen_identifiers:
                    unique_results.append(result)
                    seen_identifiers.add(identifier)
            
            parser.print_results(unique_results, keyword)
            
            if unique_results:
                save = input("\nСохранить результаты в файл? (y/n): ").strip().lower()
                if save in ['y', 'yes', 'да', 'д']:
                    parser.save_results(unique_results, keyword)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await parser.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
