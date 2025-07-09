import os
import pandas as pd
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.urls import path
from django.core.wsgi import get_wsgi_application
from visualize import generate_graphs
from db_connection import get_db
from django.core.management import execute_from_command_line
from django.conf.urls.static import static
from django.middleware.csrf import CsrfViewMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

settings.configure(
    DEBUG=True,
    SECRET_KEY='your-secret-key',
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=['*'],
    MIDDLEWARE=[
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
    ],
    INSTALLED_APPS=[
        'django.contrib.sessions',
    ],
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
    }],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    },
    STATIC_URL='/static/',
    STATICFILES_DIRS=[os.path.join(BASE_DIR, 'static')],
    MEDIA_URL='/media/',
    MEDIA_ROOT=os.path.join(BASE_DIR, 'media'),
)

db = get_db()

def login_view(request):
    if request.method == 'POST':
        data = request.POST
        user = db.users.find_one({"email": data['email'], "password": data['password']})
        if user:
            request.session['user'] = user['email']
            return redirect('/upload')
        return render(request, 'index.html', {'error': 'Invalid credentials'})
    return render(request, 'index.html')

def register_view(request):
    if request.method == 'POST':
        data = request.POST
        if db.users.find_one({'email': data['email']}):
            return render(request, 'register.html', {'error': 'User already exists'})
        db.users.insert_one(dict(data))
        return redirect('/')
    return render(request, 'register.html')

def upload_view(request):
    if 'user' not in request.session:
        return redirect('/')

    message = None
    preview_data = None
    columns = None

    if request.method == 'POST' and request.FILES.get('dataset'):
        uploaded_file = request.FILES['dataset']
        fs = FileSystemStorage(location='media/')
        filename = fs.save(uploaded_file.name, uploaded_file)

        path = fs.path(filename)
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(path)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(path, engine='openpyxl')
            else:
                message = "Unsupported file type. Please upload a CSV or XLSX file."
                return render(request, 'upload.html', {'message': message})

            # Only store the filename (not path) in session
            request.session['csv_file'] = filename
            request.session['columns'] = df.columns.tolist()

            preview_data = df.head().to_html(classes='table table-striped text-white', index=False)
            columns = df.columns.tolist()

        except Exception as e:
            message = f"Failed to read file: {str(e)}"

    return render(request, 'upload.html', {
        'message': message,
        'preview': preview_data,
        'columns': columns
    })

def visualize_view(request):
    if 'user' not in request.session:
        return redirect('/')

    if request.method == 'POST':
        filename = request.session.get('csv_file')
        fs = FileSystemStorage(location='media/')
        path = fs.path(filename)

        x_col = request.POST.get('x_col')
        y_col = request.POST.get('y_col')
        graph_type = request.POST.get('graph_type')

        if not all([path, x_col, y_col, graph_type]):
            return redirect('/upload')

        graphs = generate_graphs(path, x_col, y_col, graph_type)
        return render(request, 'visualize.html', {'graphs': graphs})

    return redirect('/upload')

def logout_view(request):
    request.session.flush()
    return redirect('/')

urlpatterns = [
    path('', login_view),
    path('register/', register_view),
    path('upload/', upload_view),
    path('visualize/', visualize_view),
    path('logout/', logout_view),
]

urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(BASE_DIR, 'static'))
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

application = SessionMiddleware(CsrfViewMiddleware(get_wsgi_application()))

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', __name__)
    execute_from_command_line()
