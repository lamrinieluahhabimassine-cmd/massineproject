"""
Script de test pour vérifier que toutes les améliorations fonctionnent
"""
from app import create_app
from models import db, User, File
from datetime import date, timedelta
import sys

def test_imports():
    """Test que tous les modules peuvent être importés"""
    print("🧪 Test 1: Import des modules...")
    
    try:
        from utils import security, audit, search, validation, statistics, export, upload, backup
        from routes import errors
        print("✅ Tous les modules importés avec succès!")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_database_models():
    """Test que tous les modèles de base de données sont corrects"""
    print("\n🧪 Test 2: Modèles de base de données...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Créer toutes les tables
            db.create_all()
            
            # Vérifier que les tables existent en utilisant l'inspector
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = ['users', 'files', 'coc_details', 'notifications']
            
            for table in expected_tables:
                if table in tables:
                    print(f"  ✅ Table '{table}' existe")
                else:
                    print(f"  ❌ Table '{table}' manquante")
                    return False
            
            print("✅ Tous les modèles de base de données OK!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur de base de données: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_error_handlers():
    """Test que les gestionnaires d'erreur sont enregistrés"""
    print("\n🧪 Test 3: Gestionnaires d'erreur...")
    
    app = create_app()
    
    try:
        # Vérifier que les erreurs sont enregistrées
        with app.test_client() as client:
            # Test 404
            response = client.get('/page-inexistante')
            if response.status_code == 404:
                print("  ✅ Erreur 404 gérée")
            else:
                print(f"  ❌ Erreur 404 non gérée (code: {response.status_code})")
                return False
        
        print("✅ Gestionnaires d'erreur OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_validation():
    """Test des fonctions de validation"""
    print("\n🧪 Test 4: Validation des données...")
    
    try:
        from utils.validation import FileValidator, UserValidator, ValidationError
        
        # Test validation de numéro de fichier
        try:
            FileValidator.validate_file_number("VOC-2025-001")
            print("  ✅ Validation numéro de fichier OK")
        except ValidationError as e:
            print(f"  ❌ Validation numéro de fichier échouée: {e}")
            return False
        
        # Test validation de route
        try:
            FileValidator.validate_route("A")
            print("  ✅ Validation route OK")
        except ValidationError as e:
            print(f"  ❌ Validation route échouée: {e}")
            return False
        
        # Test validation d'email
        try:
            UserValidator.validate_email("test@intertek.com")
            print("  ✅ Validation email OK")
        except ValidationError as e:
            print(f"  ❌ Validation email échouée: {e}")
            return False
        
        # Test validation mot de passe
        try:
            UserValidator.validate_password("Password123")
            print("  ✅ Validation mot de passe OK")
        except ValidationError as e:
            print(f"  ❌ Validation mot de passe échouée: {e}")
            return False
        
        print("✅ Validation des données OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_search():
    """Test du système de recherche"""
    print("\n🧪 Test 5: Système de recherche...")
    
    app = create_app()
    
    with app.app_context():
        try:
            from utils.search import FileSearchFilter, search_files
            
            # Test de recherche basique
            search = FileSearchFilter()
            search.by_status("Finalized")
            files = search.all()
            
            print(f"  ✅ Recherche retourne {len(files)} résultats")
            
            # Test de recherche avec filtres
            filters = {
                'status': 'Finalized',
                'route': 'A'
            }
            search_result = search_files(filters)
            files = search_result.all()
            
            print(f"  ✅ Recherche avec filtres retourne {len(files)} résultats")
            
            print("✅ Système de recherche OK!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False


def test_statistics():
    """Test du système de statistiques"""
    print("\n🧪 Test 6: Système de statistiques...")
    
    app = create_app()
    
    with app.app_context():
        try:
            from utils.statistics import Statistics, generate_dashboard_data
            
            # Test statistiques de base
            stats = Statistics.get_overview_stats()
            print(f"  ✅ Statistiques générales: {stats['total_files']} fichiers")
            
            # Test par statut
            by_status = Statistics.get_files_by_status()
            print(f"  ✅ Distribution par statut: {len(by_status)} statuts")
            
            # Test par route
            by_route = Statistics.get_files_by_route()
            print(f"  ✅ Distribution par route: {len(by_route)} routes")
            
            # Test données dashboard
            dashboard_data = generate_dashboard_data()
            print(f"  ✅ Données dashboard générées")
            
            print("✅ Système de statistiques OK!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_export():
    """Test du système d'export"""
    print("\n🧪 Test 7: Système d'export...")
    
    app = create_app()
    
    with app.app_context():
        try:
            from utils.export import export_files_to_csv, export_users_to_csv
            
            # Test export fichiers
            files = File.query.limit(5).all()
            csv_data = export_files_to_csv(files)
            
            if len(csv_data) > 0:
                print(f"  ✅ Export CSV fichiers: {len(csv_data)} caractères")
            else:
                print("  ⚠️  Export CSV fichiers vide (aucun fichier)")
            
            # Test export utilisateurs
            users = User.query.limit(5).all()
            csv_data = export_users_to_csv(users)
            
            if len(csv_data) > 0:
                print(f"  ✅ Export CSV utilisateurs: {len(csv_data)} caractères")
            else:
                print("  ❌ Export CSV utilisateurs échoué")
                return False
            
            print("✅ Système d'export OK!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False


def run_all_tests():
    """Exécuter tous les tests"""
    print("="*60)
    print("🚀 TESTS DES AMÉLIORATIONS - VOC PLATFORM")
    print("="*60)
    
    tests = [
        test_imports,
        test_database_models,
        test_error_handlers,
        test_validation,
        test_search,
        test_statistics,
        test_export
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test échoué avec exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Tests réussis: {passed}/{total} ({percentage:.1f}%)")
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS PASSÉS! L'application est prête!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) échoué(s). Vérifiez les erreurs ci-dessus.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())