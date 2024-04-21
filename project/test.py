import unittest
from unittest.mock import patch, MagicMock,mock_open
from .models import AnalysisResultt
from .tools import *
from io import StringIO
from faker import Faker
from parameterized import parameterized

class AnalysisTestCase(unittest.TestCase):
    def setUp(self):
        # Test için gereken ayarlar
        self.valid_repository_url = "https://github.com/valid/repo"
        self.invalid_repository_url = "https://github.com/invalid/repo"
        self.destination_folder = "/destination"
    def test_get_java_files(self):
        # get_java_files fonksiyonunu test et
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/java/files', (None,), ('example.java',)),
                ('/java/files/subdir', (None,), ('test.java',)),
            ]
            result = get_java_files('/path/to/java/files')
            # Dosya yollarını işletim sistemine uygun hale getir
            normalized_result = [os.path.normpath(path) for path in result]
            self.assertIn(os.path.normpath('/java/files/example.java'), normalized_result)
            self.assertIn(os.path.normpath('/java/files/subdir/test.java'), normalized_result)
            self.assertEqual(len(normalized_result), 2) #Doğru sayıda java dosyasını bulup bulmadığını kontrol eder.

class TestCloneRepository(unittest.TestCase):
    def setUp(self):                #Gerekli ayarlar uygulanır
        self.valid_url = "https://github.com/valid/repo.git"
        self.destination_folder = "/destination"


    @patch('os.path.exists', return_value=True)
    @patch('git.Repo.clone_from')
    @patch('sys.stdout', new_callable=StringIO)

    def test_clone_repository_destination_exists(self, mock_stdout, mock_clone, mock_exists):
        # Hedef klasörün zaten var olduğunu simüle et
        result = clone_repository(self.valid_url, self.destination_folder)
        
        # Fonksiyonun False döndürdüğünü kontrol et
        self.assertFalse(result)
        
        # mock_exists ve mock_clone'un doğru şekilde çağrıldığını doğrula
        mock_exists.assert_called_once_with(self.destination_folder)
        mock_clone.assert_not_called()
        
        # Çıktıyı al ve beklenen mesajın olup olmadığını kontrol et
        output = mock_stdout.getvalue()
        self.assertIn("Hedef klasör zaten var.", output)

class TestRemoveDirectory(unittest.TestCase):
    def setUp(self):
        self.directory = "/remove"

    @patch('sys.stdout', new_callable=StringIO)
    @patch('shutil.rmtree')
    def test_remove_directory_success(self, mock_rmtree,mock_stdout):
        # Klasör başarıyla silinmesi senaryosu
        remove_directory(self.directory)
        mock_rmtree.assert_called_once_with(self.directory, onerror=onerror)
        # Çıktıyı al ve beklenen mesajın olup olmadığını kontrol et
        output = mock_stdout.getvalue()
        self.assertIn("remove ve içindeki tüm dosyalar başarıyla silindi.", output)

    @patch('shutil.rmtree', side_effect=FileNotFoundError)
    def test_directory_already_removed(self, mock_rmtree):
        # Klasör zaten silinmiş senaryosu
        with self.assertRaises(FileNotFoundError):
            remove_directory(self.directory)
        mock_rmtree.assert_called_once_with(self.directory, onerror=onerror)

    #@patch('os.access', return_value=False)
    @patch('shutil.rmtree', side_effect=PermissionError("Yeterli izinler yok"))
    def test_no_permissions(self, mock_rmtree):
        # Yeterli izinlerin olmaması durumunu test et
        with self.assertRaises(PermissionError):
            remove_directory(self.directory)
        # shutil.rmtree'nin çağrıldığını doğrula
        mock_rmtree.assert_called_once_with(self.directory, onerror=onerror)

class TestOnErrorFunctionality(unittest.TestCase):
    def setUp(self):                                #Sınıf başında gerekli olan değişkenler atanıyor.
        self.path = "/path/to/faulty/directory"         
        self.func = MagicMock()

    @patch('os.access', return_value=False)
    @patch('os.chmod')
    def test_onerror_with_no_write_access(self, mock_chmod, mock_access):
        # os.access False dönerse, os.chmod çağrılır ve func tekrar çağrılır
        exc_info = (type(Exception()), Exception("Permission denied"), None)
        onerror(self.func, self.path, exc_info)
        
        mock_access.assert_called_once_with(self.path, os.W_OK) #Belirtilen yoldaki dosyanın yazılabilir olup olmadığının kontrol eder.
        mock_chmod.assert_called_once_with(self.path, stat.S_IWUSR)#İzinlerinin değiştirilerek sadece sahibin yazabileceği bir duruma getirildiğini doğrular.
        self.func.assert_called_once_with(self.path)#Bu işlemin bir kere gerçekleştiğini kontrol eder.

    @patch('os.access', return_value=True)
    def test_onerror_with_write_access(self, mock_access):
        # os.access True dönerse, hata fırlatılır
        exc_info = (type(Exception()), Exception("Permission denied"), None)
        
        with self.assertRaises(Exception):
            onerror(self.func, self.path, exc_info)
        
        mock_access.assert_called_once_with(self.path, os.W_OK)#Belirtilen yoldaki dosyanın yazılabilir olup olmadığının kontrol eder.
        self.func.assert_not_called() #Hata olmadıgından bu fonksiyonun çağrılmadığını kontrol eder.

class TestGetJavaFiles(unittest.TestCase):
    def setUp(self):
        self.test_folder = "/path/to/test/folder"

    @patch('os.walk')
    def test_with_java_files(self, mock_walk):
        # Java dosyalarının bulunduğu bir senaryo simüle ediliyor
        mock_walk.return_value = [
            (self.test_folder, ("dir1",), ("file1.java", "file2.txt")),
            (os.path.join(self.test_folder, "dir1"), (), ("file3.java", "file4.java"))
        ]
        expected_files = [
            os.path.normpath(os.path.join(self.test_folder, "file1.java")),
            os.path.normpath(os.path.join(self.test_folder, "dir1", "file3.java")),
            os.path.normpath(os.path.join(self.test_folder, "dir1", "file4.java"))
        ]
        java_files = get_java_files(self.test_folder)
        java_files = [os.path.normpath(file) for file in java_files]
        self.assertEqual(java_files, expected_files)

    @patch('os.walk')
    def test_with_no_java_files(self, mock_walk):
        # Java dosyası içermeyen bir senaryo simüle ediliyor
        mock_walk.return_value = [
            (self.test_folder, ("dir1",), ("file1.txt", "file2.doc"))
        ]
        java_files = get_java_files(self.test_folder)
        self.assertEqual(java_files, [])

    @patch('os.walk')
    def test_empty_directory(self, mock_walk):
        # Boş bir dizin simüle ediliyor
        mock_walk.return_value = [
            (self.test_folder, (), ())
        ]
        java_files = get_java_files(self.test_folder)
        self.assertEqual(java_files, [])

class TestWithFaker(unittest.TestCase):
    def setUp(self):
        self.faker = Faker()

    @patch('builtins.open', new_callable=mock_open, read_data='public class Test {}')
    def test_analyze_java_file(self, mock_file):
        # Rastgele bir dosya yolu oluştur
        fake_file_path = f"{self.faker.file_path(depth=2, extension='java')}"
        # Fonksiyonu çağır
        result = analyze_java_file(fake_file_path)
        # Sonuçların beklentilere uygun olduğunu kontrol et
        self.assertIsNotNone(result)
        self.assertIn('file_name', result)
        self.assertIn('javadoc_comment_count', result)

    
    def test_save_analysis_to_database(self):
        # Rastgele analiz sonuçları oluştur ve veritabanına kaydeder.
        analysis_results = { 
            'file_name': self.faker.file_name(extension='java'),
            'javadoc_comment_count': self.faker.random_number(),
            'other_comment_count': self.faker.random_number(),
            'code_line_count': self.faker.random_number(),
            'loc_count': self.faker.random_number(),
            'function_count': self.faker.random_number(),
            'comment_deviation_percentage': self.faker.pyfloat(right_digits=2, positive=True)
        }
        save_analysis_to_database(analysis_results)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('os.path.exists', return_value=True)
    def test_clone_repository_existing_folder(self, mock_exists,mock_stdout):#Rastgeler url ve yol üretilip fonksiyon çalıştırılır.
        repository_url = self.faker.uri()
        destination_folder = self.faker.file_path(depth=1)  
        result = clone_repository(repository_url, destination_folder)
        self.assertFalse(result)
         # Çıktıyı al ve beklenen mesajın olup olmadığını kontrol et
        output = mock_stdout.getvalue()
        self.assertIn("Hedef klasör zaten var.", output)

    @patch('os.walk')
    def test_get_java_files(self, mock_walk):           
        mock_walk.return_value = [
            ('/fake/path', ('dir1', 'dir2'), ('file1.java', 'file2.txt')),
            ('/fake/path/dir1', (), ('file3.java', 'file4.doc'))
        ]
        result = get_java_files('/fake/path')
        self.assertEqual(len(result), 2)
        self.assertTrue(all(file.endswith('.java') for file in result))

    @patch('sys.stdout', new_callable=StringIO)
    @patch('shutil.rmtree')
    def test_remove_directory(self, mock_rmtree,mock_stdout):
        # Rastgele bir dizin yolu oluştur
        fake_directory_path = self.faker.file_path(depth=2)

        # Fonksiyonu çağır
        remove_directory(fake_directory_path)

        # shutil.rmtree'nin çağrıldığını doğrula
        mock_rmtree.assert_called_once_with(fake_directory_path, onerror=onerror)

        # Ayrıca, hata yönetimi fonksiyonunun (onerror) doğru parametrelerle kullanıldığını da kontrol et
        # Bu durumda, bu kontrol mock_rmtree.assert_called_once_with içinde dolaylı olarak yapılıyor.

        # Çıktıyı al ve beklenen mesajın olup olmadığını kontrol et
        output = mock_stdout.getvalue()
        self.assertIn(fake_directory_path+" ve içindeki tüm dosyalar başarıyla silindi.", output)

class TestParameterized(unittest.TestCase): # parametre verilip fonksiyonların beklenen sonuçları mı diye doğrulama yapılıyor.
    @parameterized.expand([
        # (javaDocYorumSayisi, digerYorumSayisi, fonksiyonSayisi, kodSatirSayisi, beklenen_sonuc)
        (10, 5, 3, 100, -60),
        (0, 0, 0, 100, -100.0),  
        (20, 30, 10, 300,-55.55556),
        (1, 1, 5, 500, -98.93),
        (0, 0, 5, 500, -100.0),  
    ])
    def test_yorumSapmaYuzdesi(self, javaDoc, diger, fonksiyon, kod, expected):
        result = yorumSapmaYuzdesi(javaDoc, diger, fonksiyon, kod)
        self.assertAlmostEqual(result, expected, places=2)

    @parameterized.expand([
        ("empty string", "", 0),
        ("single line", "Hello, world!", 1),
        ("two lines", "Hello\nworld!", 2),
        ("ends with newline", "Hello, world!\n", 1),
        ("multiple newlines", "\nHello\nworld!\n", 3)
    ])
    def test_countLines(self, name, content, expected):
        result = countLines(content)
        self.assertEqual(result, expected, f"{name} should have {expected} lines, got {result}.")

    @parameterized.expand([     
        ("simple match", r"cat", "cat dog cat", 2),
        ("no match", r"bat", "cat dog cat", 0),
        ("case sensitive", r"Dog", "dog DOG Dog dOg", 1),
        ("special characters", r"\d+", "123 abc 456", 2),
        ("multiline", r"^start", "start line\nstart again\nno start", 1)
    ])
    def test_count_regex_matches(self, name, regex, content, expected_count):
        result = count_regex_matches(regex, content)
        self.assertEqual(result, expected_count)

class TestIntegration(unittest.TestCase):   #Üretilen model veritabanında bir dizi işlem gerçekleştirilerek 
                                            #veritabanı bağlantısı doğrulanmış oluyor ve bir dizi veritabanı işlemi test ediliyor.
    def setUp(self):
        AnalysisResultt.objects.create(
            file_name="testfile.java",
            javadoc_comment_count=10,
            other_comment_count=5,
            code_line_count=100,
            loc_count=120,
            function_count=3,
            comment_deviation_percentage=20.5
        )
    
    def test_create_analysis_resultt(self):
        """Model oluşturma testi"""
        result = AnalysisResultt.objects.filter(file_name="testfile.java").first()
        self.assertIsNotNone(result)
        self.assertEqual(result.file_name, "testfile.java")

    def test_update_analysis_resultt(self):
        """Model güncelleme testi"""
        result = AnalysisResultt.objects.filter(file_name="testfile.java").first()
        result.javadoc_comment_count = 15
        result.save()
        updated_result = AnalysisResultt.objects.filter(file_name="testfile.java").first()
        self.assertEqual(updated_result.javadoc_comment_count, 15)

    def test_delete_analysis_resultt(self):
        """Model silme testi"""
        result = AnalysisResultt.objects.filter(file_name="testfile.java").first()
        result.delete()
        with self.assertRaises(AnalysisResultt.DoesNotExist):
            AnalysisResultt.objects.get(file_name="testfile.java")

    def test_query_analysis_resultt_by_file_name(self):
        """Dosya adına göre model sorgulama testi"""
        result = AnalysisResultt.objects.filter(file_name="testfile.java").first()
        self.assertIsNotNone(result)
        self.assertEqual(result.file_name, "testfile.java")

    def test_str_method(self):
        """__str__ metodunun testi"""
        result = AnalysisResultt.objects.filter(file_name="testfile.java").first()
        self.assertEqual(str(result), "testfile.java")


    def tearDown(self):
        AnalysisResultt.objects.all().delete()  # Test veritabanını temizle



if __name__ == '__main__':
    unittest.main()
