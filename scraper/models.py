from django.db import models
from django.utils import timezone
import os

class Website(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ScrapedPDF(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='pdfs')
    title = models.CharField(max_length=500)
    url = models.URLField()
    file_path = models.CharField(max_length=500)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PDFDocument(models.Model):
    """
    Modèle pour stocker les PDFs analysés avec Azure OpenAI.
    """
    # Informations de base
    filename = models.CharField(max_length=255, help_text="Nom du fichier PDF")
    file_path = models.CharField(max_length=500, help_text="Chemin vers le fichier PDF")
    url = models.URLField(blank=True, null=True, help_text="URL d'origine du PDF (si applicable)")
    
    # Contenu extrait
    content = models.TextField(blank=True, null=True, help_text="Texte extrait du PDF")
    content_length = models.IntegerField(default=0, help_text="Nombre de caractères du contenu")
    
    # Analyse OpenAI
    language = models.CharField(max_length=50, blank=True, null=True, help_text="Langue détectée")
    theme = models.CharField(max_length=100, blank=True, null=True, help_text="Thématique principale")
    confidence = models.CharField(max_length=20, default='Moyen', help_text="Niveau de confiance de l'analyse")
    summary = models.TextField(blank=True, null=True, help_text="Résumé généré par IA")
    
    # Métadonnées
    file_size = models.BigIntegerField(default=0, help_text="Taille du fichier en octets")
    page_count = models.IntegerField(default=0, help_text="Nombre de pages")
    source_directory = models.CharField(max_length=200, blank=True, null=True, help_text="Répertoire source")
    
    # Statuts de traitement
    is_processed = models.BooleanField(default=False, help_text="PDF traité avec succès")
    is_retained = models.BooleanField(default=False, help_text="PDF marqué comme important")
    extraction_success = models.BooleanField(default=False, help_text="Extraction de texte réussie")
    analysis_success = models.BooleanField(default=False, help_text="Analyse OpenAI réussie")
    
    # Erreurs et logs
    error_message = models.TextField(blank=True, null=True, help_text="Message d'erreur si échec")
    processing_notes = models.TextField(blank=True, null=True, help_text="Notes de traitement")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True, help_text="Date de traitement")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Document PDF"
        verbose_name_plural = "Documents PDF"
        indexes = [
            models.Index(fields=['language']),
            models.Index(fields=['theme']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['source_directory']),
        ]
    
    def __str__(self):
        return f"{self.filename} ({self.language or 'N/A'} - {self.theme or 'N/A'})"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement certains champs."""
        if self.content:
            self.content_length = len(self.content)
        
        if self.file_path and os.path.exists(self.file_path):
            try:
                self.file_size = os.path.getsize(self.file_path)
            except OSError:
                pass
        
        if self.is_processed and not self.processed_at:
            self.processed_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        """Retourne la taille du fichier en MB."""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    @property
    def content_preview(self):
        """Retourne un aperçu du contenu (200 premiers caractères)."""
        if self.content:
            return self.content[:200] + "..." if len(self.content) > 200 else self.content
        return "Aucun contenu extrait"
    
    @property
    def status_display(self):
        """Retourne un statut lisible du document."""
        if not self.extraction_success:
            return "Échec extraction"
        elif not self.analysis_success:
            return "Échec analyse"
        elif self.is_processed:
            return "Traité avec succès"
        else:
            return "En attente"
    
    def mark_as_processed(self, success=True, error_message=None):
        """Marque le document comme traité."""
        self.is_processed = success
        self.processed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save()
    
    def get_absolute_url(self):
        """Retourne l'URL pour voir ce document."""
        from django.urls import reverse
        return reverse('scraper:pdf_detail', kwargs={'pk': self.pk})
