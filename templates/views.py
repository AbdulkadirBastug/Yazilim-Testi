from django.shortcuts import render
from .forms import GitHubRepoForm
from  project.tools import clone_repository, get_java_files,remove_directory,analyze_java_file,save_analysis_to_database
from project.models import AnalysisResultt

def index(request):
    form = GitHubRepoForm(request.POST)     #Formdan alınan repo urlsi ve gerekli değişkenler atandıktan sonra işlemler yapılıyor.
    if request.method == 'POST':
        form = GitHubRepoForm(request.POST)
        if form.is_valid():
            repository_url = form.cleaned_data['repository_url']
            destination_folder = "C:/tmp2/repo"
            remove_directory(destination_folder)#Dizinde dosya varsa hata vermemsi için önce dizin temizleniyor.
            if clone_repository(repository_url, destination_folder):#Dizine kopyalama işlemi gerçekleşir.
                java_files = get_java_files(destination_folder)#Belirtilen dizindeki sadece java dosyaları alınır.
                file_names = []
                javadoc_counts = []
                other_comment_counts = []
                code_line_counts = []
                loc_counts = []
                function_counts = []
                deviation_percentages = []

                for file in java_files:         #Her bir dosya analize gönderilir ve analiz sonuçları modelin her bir elememanı
                                                #için ayrı bir liste oluşturulup ilgili listelere kaydedilir.
                    results = analyze_java_file(file)
                    save_analysis_to_database(results)
                    file_names.append((results['file_name']))
                    javadoc_counts.append(results['javadoc_comment_count'])
                    other_comment_counts.append(results['other_comment_count'])
                    code_line_counts.append(results['code_line_count'])
                    loc_counts.append(results['loc_count'])
                    function_counts.append(results['function_count'])
                    deviation_percentages.append(results['comment_deviation_percentage'])
                #Bu listedekiler tek bir yerde birleştirlir ve result.html e zipped_results olarak gönderilir.
                zipped_results = zip(file_names, javadoc_counts, other_comment_counts, code_line_counts, loc_counts, function_counts, deviation_percentages)
                return render(request, 'result.html', {'zipped_results': zipped_results})
            
                #Burada üstteki işlemlerin aynısı veritabanındaki dosyaları çekmek için uygulanır.
    results2 = AnalysisResultt.objects.all()
    file_names2 = []
    javadoc_counts2 = []
    other_comment_counts2 = []
    code_line_counts2 = []
    loc_counts2 = []
    function_counts2 = []
    deviation_percentages2 = []

    for result in results2:
        file_names2.append(result.file_name)  
        javadoc_counts2.append(result.javadoc_comment_count)  
        other_comment_counts2.append(result.other_comment_count)  
        code_line_counts2.append(result.code_line_count)  
        loc_counts2.append(result.loc_count)  
        function_counts2.append(result.function_count)  
        deviation_percentages2.append(result.comment_deviation_percentage)  

    zipped_results2 = zip(file_names2, javadoc_counts2, other_comment_counts2, code_line_counts2, loc_counts2, function_counts2, deviation_percentages2)
    return render(request, 'index.html', {'form': form, 'zipped_results2': zipped_results2})
