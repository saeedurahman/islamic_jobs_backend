from django.db import models
from django.utils.text import slugify


class Province(models.Model):
    name = models.CharField(max_length=100)
    name_urdu = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class City(models.Model):
    name = models.CharField(max_length=100)
    name_urdu = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        related_name='cities',
    )

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'cities'

    def __str__(self):
        return f'{self.name}, {self.province.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while City.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class District(models.Model):
    name = models.CharField(max_length=100)
    name_urdu = models.CharField(max_length=100)
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='districts',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.city.name}'


class Village(models.Model):
    name = models.CharField(max_length=100)
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name='villages',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.district.name}'
