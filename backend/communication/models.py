from django.conf import settings
from django.db import models
class Notice(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, default="ALL", help_text="ALL, STUDENT, FACULTY, or PARENT")
    published_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="notices")
    class Meta: ordering = ("-published_at",)


class NoticeRecipient(models.Model):
    recipient_id = models.BigAutoField(primary_key=True)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name="recipients")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notice_recipients")
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)


class Post(models.Model):
    post_id = models.BigAutoField(primary_key=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200)
    content = models.TextField()
    image_url = models.URLField(blank=True)
    visibility = models.CharField(max_length=30, default="ALL")
    created_at = models.DateTimeField(auto_now_add=True)


class PostComment(models.Model):
    comment_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("post", "user"), name="unique_post_like")]


class Notification(models.Model):
    notification_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class MessageLog(models.Model):
    message_log_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="message_logs")
    channel = models.CharField(max_length=10, choices=(("EMAIL", "Email"), ("SMS", "SMS")))
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=30, default="PENDING")
    sent_at = models.DateTimeField(null=True, blank=True)


class ServiceRequest(models.Model):
    request_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="service_requests")
    request_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, default="PENDING")
    response = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Event(models.Model):
    event_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    venue = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="event_registrations")
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default="REGISTERED")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("event", "student"), name="unique_event_student")]


class Club(models.Model):
    club_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class ClubMembership(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="club_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default="PENDING")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("club", "student"), name="unique_club_student")]
