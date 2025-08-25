from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import F, Avg, Count, Sum
from django.contrib import messages
from .models import Quote, Source
from .forms import QuoteForm, SourceForm
import random
from django.utils import timezone
from datetime import timedelta

def get_random_quote(request):
    try:
        quotes = Quote.objects.all()
        if not quotes.exists():
            return render(request, 'quotes/no_quotes.html')

        # Weighted random selection using proper algorithm
        quotes_list = list(quotes)
        weights = []
        for quote in quotes_list:
            base_weight = quote.weight
            like_factor = max(0, quote.likes - quote.dislikes * 0.5)
            total_weight = base_weight * 10 + like_factor * 2
            weights.append(max(1, total_weight))

        total_weight = sum(weights)
        if total_weight <= 0:
            random_quote = random.choice(quotes_list)
        else:
            random_value = random.uniform(0, total_weight)
            cumulative_weight = 0
            random_quote = quotes_list[-1]  # Default to last if nothing matches
            for quote, weight in zip(quotes_list, weights):
                cumulative_weight += weight
                if random_value <= cumulative_weight:
                    random_quote = quote
                    break

        # Increment view count
        Quote.objects.filter(id=random_quote.id).update(views=F('views') + 1)
        random_quote.refresh_from_db()

        context = {
            'quote': random_quote,
            'source': random_quote.source,
            'total_quotes': len(quotes_list)
        }
        return render(request, 'quotes/random_quote.html', context)

    except Quote.DoesNotExist:
        return render(request, 'quotes/no_quotes.html')

def get_popular_quotes(request):
    try:
        # Получаем параметры фильтрации
        sort_by = request.GET.get('sort_by', 'likes')
        source_filter = request.GET.get('source', '')
        
        # Базовый запрос
        quotes = Quote.objects.all()
        
        # Применяем фильтр по источнику, если указан
        if source_filter:
            quotes = quotes.filter(source__name__icontains=source_filter)
        
        # Сортировка по выбранному полю
        if sort_by == 'views':
            quotes = quotes.order_by('-views')
        elif sort_by == 'weight':
            quotes = quotes.order_by('-weight')
        elif sort_by == 'newest':
            quotes = quotes.order_by('-id')
        else:  # По умолчанию сортируем по лайкам
            quotes = quotes.order_by('-likes')
        
        # Получаем топ-10 цитат
        popular_quotes = quotes[:10]
        
        # Получаем все источники для фильтра
        all_sources = Source.objects.all()
        
        context = {
            'popular_quotes': popular_quotes,
            'all_sources': all_sources,
            'current_sort': sort_by,
            'current_source': source_filter
        }
        return render(request, 'quotes/popular_quotes.html', context)

    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return render(request, 'quotes/no_quotes.html')

def add_quote_view(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        source_name = request.POST.get('source')
        weight = request.POST.get('weight', 1)

        try:
            source, created = Source.objects.get_or_create(name=source_name)
            
            # Check if source has too many quotes
            if source.quote_set.count() >= 3:
                return JsonResponse({'error': f"Source '{source_name}' already has 3 quotes."})

            # Check for duplicate quote
            if Quote.objects.filter(text=text, source=source).exists():
                return JsonResponse({'error': 'Duplicate quote for this source.'})

            quote = Quote.objects.create(
                text=text,
                source=source,
                weight=int(weight)
            )
            return JsonResponse({'success': True, 'quote_id': quote.id})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        quote_form = QuoteForm()
        source_form = SourceForm()
    
    return render(request, 'quotes/add_quote.html', {
        'quote_form': quote_form,
        'source_form': source_form
    })

def like_quote(request, quote_id):
    if request.method == 'POST':
        quote = get_object_or_404(Quote, id=quote_id)
        Quote.objects.filter(id=quote_id).update(likes=F('likes') + 1)
        quote.refresh_from_db()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'likes': quote.likes})
        return redirect('random_quote')
    return redirect('random_quote')

def dislike_quote(request, quote_id):
    if request.method == 'POST':
        quote = get_object_or_404(Quote, id=quote_id)
        Quote.objects.filter(id=quote_id).update(dislikes=F('dislikes') + 1)
        quote.refresh_from_db()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'dislikes': quote.dislikes})
        return redirect('random_quote')
    return redirect('random_quote')


def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            try:
                quote = form.save(commit=False)
                
                # Check for duplicate quote text
                if Quote.objects.filter(text=quote.text).exists():
                    messages.error(request, 'Эта цитата уже добавлена!')
                    return render(request, 'quotes/add_quote.html', {'form': form})
                
                # Check 3-quotes-per-source constraint
                source_quotes_count = Quote.objects.filter(source=quote.source).count()
                if source_quotes_count >= 3:
                    messages.error(request, f'Нельзя добавить более 3 цитат на 1 источник!')
                    return render(request, 'quotes/add_quote.html', {'form': form})
                
                quote.save()
                messages.success(request, f'Цитата успешно добавлена!')
                return redirect('random_quote')
                
            except Exception as e:
                messages.error(request, f'Ошибка добавления цитаты: {str(e)}')
    else:
        form = QuoteForm()
    return render(request, 'quotes/add_quote.html', {'form': form})


def add_source(request):
    if request.method == 'POST':
        form = SourceForm(request.POST)
        if form.is_valid():
            try:
                source = form.save()
                messages.success(request, f'Источник "{source.name}" успещно добавлен!')
                return redirect('add_quote')
            except Exception as e:
                messages.error(request, f'Ошибка добавления источника: {str(e)}')
    else:
        form = SourceForm()
    return render(request, 'quotes/add_source.html', {'form': form})

def dashboard(request):
    try:
        # General statistics
        total_quotes = Quote.objects.count()
        total_sources = Source.objects.count()
        total_views = Quote.objects.aggregate(total=Avg('views'))['total'] or 0
        total_likes = Quote.objects.aggregate(total=Avg('likes'))['total'] or 0

        # Top quotes by likes
        top_quotes = Quote.objects.order_by('-likes')[:10]

        # Sources with most quotes
        sources_with_most_quotes = Source.objects.annotate(quote_count=Count('quote')).order_by('-quote_count')[:5]

        # Recent quotes
        recent_quotes = Quote.objects.order_by('-id')[:5]

        # Most viewed quotes
        most_viewed = Quote.objects.order_by('-views')[:5]

        context = {
            'total_quotes': total_quotes,
            'total_sources': total_sources,
            'total_views': total_views,
            'total_likes': total_likes,
            'top_quotes': top_quotes,
            'sources_with_most_quotes': sources_with_most_quotes,
            'recent_quotes': recent_quotes,
            'most_viewed': most_viewed,
        }
        return render(request, 'quotes/dashboard.html', context)
    except Exception as e:
        return render(request, 'quotes/error.html', {'error': str(e)})
