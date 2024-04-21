
from django.db import models

class AnalysisResultt(models.Model):
    file_name = models.CharField(max_length=255, default='Unknown')
    javadoc_comment_count = models.IntegerField()
    other_comment_count = models.IntegerField()
    code_line_count = models.IntegerField()
    loc_count = models.IntegerField()
    function_count = models.IntegerField()
    comment_deviation_percentage = models.FloatField()

    def __str__(self):
        return self.file_name