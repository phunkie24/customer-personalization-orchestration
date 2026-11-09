"""
Generate synthetic data for the personalization system
- 500,000 customer records
- 5,000 marketing content pieces
"""
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import json
import os

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)


class DataGenerator:
    def __init__(self, output_dir="../data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_customers(self, num_customers=500000):
        """Generate customer dataset"""
        print(f"Generating {num_customers} customer records...")
        
        customers = []
        product_categories = ['Electronics', 'Fashion', 'Home', 'Beauty', 'Sports', 'Books', 'Toys']
        
        for i in range(num_customers):
            if i % 50000 == 0:
                print(f"  Generated {i} customers...")
            
            # Demographics
            age = np.random.normal(40, 15)
            age = max(18, min(80, int(age)))
            
            # Income based on age
            base_income = 30000 + (age - 18) * 1000
            income = max(20000, np.random.normal(base_income, 25000))
            
            # Purchase behavior
            purchase_frequency = np.random.poisson(5)
            average_order_value = np.random.gamma(2, 50)
            lifetime_value = purchase_frequency * average_order_value * np.random.uniform(1, 5)
            
            # Recency
            recency_days = int(np.random.exponential(30))
            
            # Engagement
            engagement_score = np.random.beta(2, 5)
            
            # Product preferences
            num_categories = np.random.randint(1, 4)
            preferred_categories = random.sample(product_categories, num_categories)
            
            customer = {
                'customer_id': f'C{str(i+1).zfill(8)}',
                'age': age,
                'income': round(income, 2),
                'purchase_frequency': purchase_frequency,
                'average_order_value': round(average_order_value, 2),
                'lifetime_value': round(lifetime_value, 2),
                'recency_days': recency_days,
                'product_categories': ','.join(preferred_categories),
                'engagement_score': round(engagement_score, 3),
                'registration_date': (datetime.now() - timedelta(days=random.randint(30, 1000))).strftime('%Y-%m-%d'),
                'email': fake.email(),
                'city': fake.city(),
                'state': fake.state_abbr(),
            }
            customers.append(customer)
        
        df = pd.DataFrame(customers)
        output_file = os.path.join(self.output_dir, 'customers.csv')
        df.to_csv(output_file, index=False)
        print(f"✓ Saved {len(df)} customers to {output_file}")
        
        # Save summary statistics
        stats = {
            'total_customers': len(df),
            'avg_age': float(df['age'].mean()),
            'avg_income': float(df['income'].mean()),
            'avg_ltv': float(df['lifetime_value'].mean()),
            'avg_purchase_frequency': float(df['purchase_frequency'].mean()),
        }
        stats_file = os.path.join(self.output_dir, 'customer_stats.json')
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"✓ Saved statistics to {stats_file}")
        
        return df
    
    def generate_content(self, num_content=5000):
        """Generate marketing content dataset"""
        print(f"Generating {num_content} content pieces...")
        
        content_pieces = []
        content_types = ['email_template', 'sms_template', 'push_notification', 'social_post']
        categories = ['product_launch', 'promotion', 'seasonal', 'educational', 'retention', 'welcome']
        products = ['Smartphone', 'Laptop', 'Headphones', 'Smartwatch', 'Tablet', 'Camera', 
                   'Dress', 'Shoes', 'Bag', 'Jacket', 'Furniture', 'Appliance']
        
        # Marketing message templates
        templates = [
            "Discover our latest {product} with {feature}. {call_to_action}",
            "Exclusive offer: {discount}% off on {product}. {call_to_action}",
            "New arrival: {product} designed for {audience}. {call_to_action}",
            "Limited time: Get {product} with free {bonus}. {call_to_action}",
            "Upgrade your {category} with our premium {product}. {call_to_action}",
        ]
        
        features = ['cutting-edge technology', 'innovative design', 'premium quality', 
                   'enhanced performance', 'elegant style', 'superior comfort']
        audiences = ['professionals', 'tech enthusiasts', 'fashion lovers', 'home makers', 
                    'fitness enthusiasts', 'students']
        ctas = ['Shop now', 'Learn more', 'Explore collection', 'Get yours today', 'View details']
        bonuses = ['shipping', 'accessories', 'warranty', 'gift card', 'installation']
        
        for i in range(num_content):
            if i % 1000 == 0:
                print(f"  Generated {i} content pieces...")
            
            template = random.choice(templates)
            product = random.choice(products)
            
            text = template.format(
                product=product,
                feature=random.choice(features),
                call_to_action=random.choice(ctas),
                discount=random.choice([10, 15, 20, 25, 30]),
                audience=random.choice(audiences),
                category=random.choice(['experience', 'lifestyle', 'workspace', 'home']),
                bonus=random.choice(bonuses)
            )
            
            content = {
                'content_id': f'CNT{str(i+1).zfill(8)}',
                'title': f'{product} {random.choice(["Campaign", "Promotion", "Launch", "Sale"])}',
                'text': text,
                'content_type': random.choice(content_types),
                'category': random.choice(categories),
                'tags': ','.join(random.sample(['sale', 'new', 'premium', 'exclusive', 'limited', 'popular'], k=3)),
                'product': product,
                'target_segment': random.choice(['high_value', 'medium_value', 'low_value', 'tech_enthusiast', 'budget_conscious']),
                'compliance_approved': random.choice([True, True, True, False]),  # 75% approved
                'tone': random.choice(['professional', 'casual', 'friendly', 'urgent']),
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
                'performance_score': round(random.uniform(0.5, 1.0), 3),
            }
            content_pieces.append(content)
        
        df = pd.DataFrame(content_pieces)
        output_file = os.path.join(self.output_dir, 'content.csv')
        df.to_csv(output_file, index=False)
        print(f"✓ Saved {len(df)} content pieces to {output_file}")
        
        # Save as JSONL for vector DB
        jsonl_file = os.path.join(self.output_dir, 'content.jsonl')
        with open(jsonl_file, 'w') as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict()) + '\n')
        print(f"✓ Saved content in JSONL format to {jsonl_file}")
        
        return df
    
    def generate_experiment_history(self, num_experiments=100):
        """Generate historical experiment data"""
        print(f"Generating {num_experiments} historical experiments...")
        
        experiments = []
        for i in range(num_experiments):
            num_variants = random.randint(2, 4)
            
            experiment = {
                'experiment_id': f'EXP{str(i+1).zfill(8)}',
                'experiment_name': f'Campaign_{i+1}',
                'start_date': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
                'end_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'num_variants': num_variants,
                'sample_size': random.randint(1000, 10000),
                'winning_variant': chr(65 + random.randint(0, num_variants-1)),  # A, B, C, etc.
                'lift': round(random.uniform(0.05, 0.30), 3),
                'confidence': round(random.uniform(0.85, 0.99), 3),
            }
            experiments.append(experiment)
        
        df = pd.DataFrame(experiments)
        output_file = os.path.join(self.output_dir, 'experiments.csv')
        df.to_csv(output_file, index=False)
        print(f"✓ Saved {len(df)} experiments to {output_file}")
        
        return df


def main():
    """Main data generation function"""
    print("=" * 60)
    print("Customer Personalization Orchestrator - Data Generation")
    print("=" * 60)
    
    generator = DataGenerator(output_dir="data")
    
    # Generate all datasets
    customers_df = generator.generate_customers(num_customers=500000)
    content_df = generator.generate_content(num_content=5000)
    experiments_df = generator.generate_experiment_history(num_experiments=100)
    
    print("\n" + "=" * 60)
    print("Data Generation Complete!")
    print("=" * 60)
    print(f"Customers: {len(customers_df):,}")
    print(f"Content Pieces: {len(content_df):,}")
    print(f"Historical Experiments: {len(experiments_df):,}")
    print("\nData saved in ./data/ directory")
    print("Ready for Docker deployment!")


if __name__ == "__main__":
    main()
