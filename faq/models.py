from django.db import models


class MainTopic(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Main Topic"
        verbose_name_plural = "Main Topics"
        ordering = ['name']

    def __str__(self):
        return self.name


class SubTopic(models.Model):
    main_topic = models.ForeignKey(
        MainTopic,
        on_delete=models.CASCADE,
        related_name='sub_topics'
    )
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Sub Topic"
        verbose_name_plural = "Sub Topics"
        unique_together = ('main_topic', 'name')
        ordering = ['main_topic__name', 'name']

    def __str__(self):
        return f"{self.main_topic.name} > {self.name}"


class FAQ(models.Model):
    main_topic = models.ForeignKey(
        MainTopic,
        on_delete=models.CASCADE,
        related_name='faqs'
    )
    sub_topic = models.ForeignKey(
        SubTopic,
        on_delete=models.CASCADE,
        related_name='faqs'
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['main_topic__name', 'sub_topic__name', 'question']

    def __str__(self):
        return f"{self.question[:60]}{'...' if len(self.question) > 60 else ''}"
