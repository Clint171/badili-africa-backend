from django.db import models

class FundingSource(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    guidelines = models.TextField()

    def __str__(self):
        return self.name

class Stipulation(models.Model):
    funding_source = models.ForeignKey(FundingSource, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    timeline = models.DateField()

    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=255)
    funding_source = models.ForeignKey(FundingSource, on_delete=models.CASCADE)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.title

class CostCenter(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name
