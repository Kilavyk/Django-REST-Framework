from rest_framework.pagination import PageNumberPagination

class LessonPagination(PageNumberPagination):
    page_size = 5  # Количество по умолчанию
    page_size_query_param = 'page_size'
    max_page_size = 50  # Максимальное количество элементов на странице

class CoursePagination(PageNumberPagination):
    page_size = 5  # Количество по умолчанию
    page_size_query_param = 'page_size'
    max_page_size = 50  # Максимальное количество элементов на странице
