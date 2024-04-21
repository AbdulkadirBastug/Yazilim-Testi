import os,shutil,git,stat,re,glob

import git.exc
from .models import AnalysisResultt

def analyze_java_file(file_path):
    """
    Java dosyasını analiz eder. Dosya içerisinde 'class' anahtar kelimesi varsa analiz işlemini gerçekleştirir.
    """
    with open(file_path, 'r') as file:
        content = file.read()
        #if 'class ' not in content:  # 'class' kelimesini kontrol et  !!! Burası runtimeda arada sırada soruna sebep olduğundan çıkarıldı.
         #   return None  # Eğer 'class' kelimesi yoksa analiz yapılmaz

    lines = content.splitlines()
    
    javadoc_comment_count = count_javadoc_comments(lines)
    other_comment_count = count_comments(lines) - javadoc_comment_count
    code_line_count = count_code_lines(content)
    loc_count = len(lines)
    function_count = count_regex_matches("(public|private|protected).*\\(.*\\)[^{]*\\{", content)
    comment_deviation_percentage = yorumSapmaYuzdesi(javadoc_comment_count, other_comment_count, function_count, code_line_count)

    file_name_only = os.path.basename(file_path)

    # Analiz sonuçlarını bir sözlük olarak da döndür
    return {
        'file_name': file_name_only,
        'javadoc_comment_count': javadoc_comment_count,
        'other_comment_count': other_comment_count,
        'code_line_count': code_line_count,
        'loc_count': loc_count,
        'function_count': function_count,
        'comment_deviation_percentage': comment_deviation_percentage
    }

def save_analysis_to_database(analysis_results):
    # Veritabanına kayıt işlemini gerçekleştir
    analysis_result = AnalysisResultt(
        file_name=analysis_results['file_name'],
        javadoc_comment_count=analysis_results['javadoc_comment_count'],
        other_comment_count=analysis_results['other_comment_count'],
        code_line_count=analysis_results['code_line_count'],
        loc_count=analysis_results['loc_count'],
        function_count=analysis_results['function_count'],
        comment_deviation_percentage=analysis_results['comment_deviation_percentage']
    )
    analysis_result.save()

def onerror(func, path, exc_info):
    
    #Silmede hata çıkarsa bu fonksiyon çalışıyor.

    # Erişim izinlerini değiştirip silme işleminin hata vermesini önlüyor.
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def remove_directory(directory):  # Silmek istediğiniz dizin eğer hata çıkarsa onerror fonk çalışır.
    
    shutil.rmtree(directory,onerror=onerror)
    print(f"{directory} ve içindeki tüm dosyalar başarıyla silindi.")

    
def clone_repository(repository_url, destination_folder):
    # Hedef klasör var mı kontrol et
    if os.path.exists(destination_folder):
        print("Hedef klasör zaten var.")
        return False

    # Hedef klasör için yazma izinlerini kontrol et
    # if not os.access(destination_folder, os.W_OK):        !!destination klasörü olmayınca sorun çıkarıyor o yüzden comment altına alındı.
    #     print("Yazma izinleri yok.")
    #     return False
    
    try:
        git.Repo.clone_from(repository_url, destination_folder)
        return True 
    except git.exc.GitCommandError:  # Git komutu ile ilgili hataları ele al
        print("Klonlama başarısız; git komutu hatası.")
        return False
    except Exception as e:  # Diğer tüm hataları ele al
        print(f"Klonlama başarısız; beklenmedik hata: {e}")
        return False

def get_java_files(folder):
    java_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".java"):              #java ile biten dosyaları java files listesine ekliyor.
                java_files.append(os.path.join(root, file))
    return java_files

def count_javadoc_comments(lines):
   #Javadoc yorum satırlarını sayar.
    
    javadoc_comment_count = 0
    in_javadoc = False
    for line in lines:
        line = line.strip()
        if not in_javadoc and line.startswith("/**"):
            in_javadoc = True
        if in_javadoc:
            javadoc_comment_count += 1
            if line.endswith("*/"):
                in_javadoc = False
    return javadoc_comment_count

def count_code_lines(content): #Verilen metindeki içerikleri line lara bölüp boşlukları eleyerek kod satır sayısını buluyor.
    lines = content.splitlines()
    count = 0
    for line in lines:
        if line.strip():
            count += 1
    return count

def count_regex_matches(regex, content):#Verilen içerikle regexin kaç defa eşleştiğinin sayısını döndürüyor.
    matches = re.findall(regex, content)
    return len(matches)

def countLines(content):     #Verilen içeriğin toplam satır sayısını buluyor.
    return len(content.splitlines())

def count_comments(lines):

   # Tüm yorum satırlarını sayar.
    
    comment_count = 0
    in_comment = False
    for line in lines:
        line = line.strip()
        if line.startswith("//"):
            comment_count += 1
        elif line.startswith("/*"):
            in_comment = True
            comment_count += 1
        elif "*/" in line:
            comment_count += 1
            in_comment = False
        elif in_comment:
            comment_count += 1
    return comment_count

def yorumSapmaYuzdesi(javaDocYorumSayisi, digerYorumSayisi, fonksiyonSayisi, kodSatirSayisi):#Yorum sapma yüzdesini hesaplayan fonksiyon
        if fonksiyonSayisi == 0:
            fonksiyonSayisi = 1
        YG = ((javaDocYorumSayisi + digerYorumSayisi) * 0.8) / fonksiyonSayisi
        YH = (kodSatirSayisi / fonksiyonSayisi) * 0.3
        return ((100 * YG) / YH) - 100
