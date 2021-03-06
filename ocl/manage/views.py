import logging

from celery.result import AsyncResult
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from manage import serializers
from tasks import find_broken_references, bulk_import

logger = logging.getLogger('oclapi')

class ManageBrokenReferencesView(viewsets.ViewSet):

    serializer_class = serializers.ReferenceSerializer

    def initial(self, request, *args, **kwargs):
        self.permission_classes = (IsAdminUser, )
        super(ManageBrokenReferencesView, self).initial(request, *args, **kwargs)

    def list(self, request):
        task = AsyncResult(request.GET.get('task'))

        if task.successful():
            broken_references = task.get()
            serializer = serializers.ReferenceListSerializer(
                instance=broken_references)
            return Response(serializer.data)
        elif task.failed():
            return Response({'exception': str(task.result)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'task': task.id, 'state': task.state})

    def post(self, request):
        task = find_broken_references.delay()

        return Response({'task': task.id, 'state': task.state})

    def delete(self, request):
        force = request.GET.get('force')
        if not force:
            force = False
        task = AsyncResult(request.GET.get('task'))

        if task.successful():
            broken_references = task.get()

            broken_references.delete(force)

            serializer = serializers.ReferenceListSerializer(
                instance=broken_references)
            return Response(serializer.data)
        elif task.failed():
            return Response({'exception': str(task.result)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'state': task.state}, status=status.HTTP_204_NO_CONTENT)


class BulkImportView(viewsets.ViewSet):

    serializer_class = serializers.OclImportResultsSerializer

    def initial(self, request, *args, **kwargs):
        self.permission_classes = (IsAdminUser, )
        super(BulkImportView, self).initial(request, *args, **kwargs)

    def list(self, request):
        task = AsyncResult(request.GET.get('task'))

        if task.successful():
            result = task.get()
            serializer = serializers.OclImportResultsSerializer(
                instance=result)
            return Response(serializer.data)
        elif task.failed():
            return Response({'exception': str(task.result)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'task': task.id, 'state': task.state})


    def post(self, request):
        task = bulk_import.delay(request.body)

        return Response({'task': task.id, 'state': task.state})