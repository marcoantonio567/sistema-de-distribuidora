from django.core.management.base import BaseCommand
from products.models import Category, Brand, Product
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de teste (Categorias, Marcas e Produtos)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando criação de dados de teste...')
        
        # 1. Criar Categorias
        categories_data = [
            'Bebidas', 
            'Alimentos', 
            'Limpeza', 
            'Higiene Pessoal', 
            'Utilidades Domésticas'
        ]
        
        categories = []
        for name in categories_data:
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': f'Produtos da categoria {name}'}
            )
            categories.append(cat)
            if created:
                self.stdout.write(f'Categoria criada: {name}')
            
        # 2. Criar Marcas
        brands_data = [
            'Marca Top', 
            'Distribuidora Plus', 
            'Qualidade Premium', 
            'Econômica', 
            'Importados'
        ]
        
        brands = []
        for name in brands_data:
            brand, created = Brand.objects.get_or_create(
                name=name,
                defaults={'description': f'Produtos da marca {name}'}
            )
            brands.append(brand)
            if created:
                self.stdout.write(f'Marca criada: {name}')
                
        # 3. Criar Produtos (Serviços/Itens)
        # Lista de tuplas: (Nome, Preço Base, Categoria Index)
        products_list = [
            ('Refrigerante Cola 2L', 8.50, 0),
            ('Suco de Laranja 1L', 6.90, 0),
            ('Água Mineral 500ml', 1.50, 0),
            ('Arroz Branco 5kg', 24.90, 1),
            ('Feijão Carioca 1kg', 8.50, 1),
            ('Macarrão Espaguete 500g', 4.20, 1),
            ('Óleo de Soja 900ml', 5.90, 1),
            ('Detergente Líquido 500ml', 2.50, 2),
            ('Sabão em Pó 1kg', 12.90, 2),
            ('Desinfetante Lavanda 2L', 7.90, 2),
            ('Shampoo Hidratante 350ml', 15.90, 3),
            ('Sabonete em Barra 90g', 1.80, 3),
            ('Papel Higiênico 12 rolos', 18.90, 3),
            ('Pano de Prato Algodão', 3.50, 4),
            ('Esponja de Aço', 2.20, 4),
        ]
        
        count = 0
        for name, price, cat_idx in products_list:
            if not Product.objects.filter(name=name).exists():
                category = categories[cat_idx]
                brand = random.choice(brands)
                
                Product.objects.create(
                    name=name,
                    category=category,
                    brand=brand,
                    price=Decimal(price),
                    description=f'Descrição detalhada do produto {name}. Ideal para o dia a dia.',
                    stock_quantity=random.randint(10, 200),
                    is_active=True,
                    is_featured=random.choice([True, False]),
                    weight=Decimal(random.uniform(0.1, 5.0)).quantize(Decimal('0.01')),
                    length=Decimal(random.randint(10, 50)),
                    width=Decimal(random.randint(10, 50)),
                    height=Decimal(random.randint(10, 50))
                )
                self.stdout.write(f'Produto criado: {name}')
                count += 1
            else:
                self.stdout.write(f'Produto já existe: {name}')
                
        self.stdout.write(self.style.SUCCESS(f'Processo finalizado! {count} novos produtos criados.'))
