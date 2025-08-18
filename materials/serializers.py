from rest_framework import serializers

from materials.models import Course, Lesson
from materials.validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"
        extra_kwargs = {
            'video_link': {'validators': [validate_youtube_url]}
        }

    def validate_video_link(self, value):
        """Дополнительная валидация для video_link"""
        if value is None:
            return value
        validate_youtube_url(value)
        return value


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True, source='lessons.all')
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Course
        fields = ["id", "title", "preview", "description", "lessons_count", "lessons", "owner"]

    def get_lessons_count(self, obj):
        return obj.lessons.count()
