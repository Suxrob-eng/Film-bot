import random
from datetime import datetime
from database import get_all_movies

class MovieStats:
    @staticmethod
    def get_random_top_movies(count=5):
        """Tasodifiy top filmlarni qaytaradi"""
        all_movies = get_all_movies()
        
        if not all_movies:
            return []
        
        if count >= len(all_movies):
            return random.sample(all_movies, len(all_movies))
        
        return random.sample(all_movies, count)
    
    @staticmethod
    def get_today_top_movies(count=3):
        """Bugungi top filmlarni qaytaradi"""
        all_movies = get_all_movies()
        
        if not all_movies:
            return []
        
        today = datetime.now().date()
        random.seed(str(today))
        
        if count >= len(all_movies):
            return random.sample(all_movies, len(all_movies))
        
        return random.sample(all_movies, count)
    
    @staticmethod
    def get_weekly_top_movies(count=5):
        """Haftalik top filmlarni qaytaradi"""
        all_movies = get_all_movies()
        
        if not all_movies:
            return []
        
        week_number = datetime.now().isocalendar()[1]
        random.seed(f"week_{week_number}")
        
        if count >= len(all_movies):
            return random.sample(all_movies, len(all_movies))
        
        return random.sample(all_movies, count)
    
    @staticmethod
    def get_popular_by_genre():
        """Janr bo'yicha mashhur filmlarni guruhlab qaytaradi"""
        all_movies = get_all_movies()
        
        if not all_movies:
            return {}
        
        genre_movies = {}
        
        for code, desc in all_movies:
            genre = "Noma'lum"
            for line in desc.split('\n'):
                if "Janri:" in line:
                    genre = line.split("Janri:")[1].strip()
                    break
            
            if genre not in genre_movies:
                genre_movies[genre] = []
            
            genre_movies[genre].append((code, desc))
        
        result = {}
        for genre, movies in genre_movies.items():
            if len(movies) <= 2:
                result[genre] = movies
            else:
                result[genre] = random.sample(movies, 2)
        
        return result
    
    @staticmethod
    def get_recommended_movie(user_id=None):
        """Foydalanuvchi uchun tavsiya etilgan film"""
        all_movies = get_all_movies()
        
        if not all_movies:
            return None
        
        if user_id:
            random.seed(str(user_id))
        
        return random.choice(all_movies)
    
    @staticmethod
    def format_movie_stats(movies_list, title="🎬 Tasodifiy Top Filmlar"):
        """Film ro'yxatini formatda qaytaradi"""
        if not movies_list:
            return "📭 Hozircha filmlar mavjud emas"
        
        response = f"{title}:\n\n"
        
        for i, (code, desc) in enumerate(movies_list, 1):
            desc_lines = desc.split('\n')
            film_title = desc_lines[0] if desc_lines else "Nomsiz film"
            
            genre = "Noma'lum"
            for line in desc_lines:
                if "Janri:" in line:
                    genre = line.split("Janri:")[1].strip()
                    break
            
            response += f"{i}. <b>{film_title}</b>\n"
            response += f"   🎭 {genre}\n"
            response += f"   🔢 Kodi: <code>{code}</code>\n\n"
        
        return response
    
    @staticmethod
    def format_genre_stats(genre_dict):
        """Janr bo'yicha filmlarni formatda qaytaradi"""
        if not genre_dict:
            return "📭 Janrlar bo'yicha filmlar topilmadi"
        
        response = "🎭 Janrlar bo'yicha Top Filmlar:\n\n"
        
        for genre, movies in genre_dict.items():
            response += f"<b>#{genre}</b>\n"
            
            for code, desc in movies:
                desc_lines = desc.split('\n')
                film_title = desc_lines[0] if desc_lines else "Nomsiz film"
                
                response += f"   • {film_title}\n"
                response += f"     🔢 Kodi: <code>{code}</code>\n"
            
            response += "\n"
        
        return response