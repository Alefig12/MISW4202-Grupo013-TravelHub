from faker import Faker
import random
from . import create_app, db
from .models import Accommodation

fake = Faker()

ROOM_TYPES = ['Single', 'Double', 'Suite', 'Penthouse', 'Studio', 'Villa', 'Cabin', 'Hostel']
AMENITIES_LIST = ['WiFi', 'Pool', 'Gym', 'Parking', 'Breakfast', 'AC', 'TV', 'Kitchen', 'Balcony', 'Pet Friendly']

def generate_amenities():
    num_amenities = random.randint(2, 6)
    return ', '.join(random.sample(AMENITIES_LIST, num_amenities))

def seed_database():
    app = create_app()
    with app.app_context():
        db.create_all()

        existing_count = Accommodation.query.count()
        if existing_count >= 1000:
            print(f"Database already has {existing_count} records. Skipping seed.")
            return

        print("Seeding database with 1000 accommodations...")

        accommodations = []
        for i in range(1000):
            accommodation = Accommodation(
                name=f"{fake.company()} {random.choice(['Hotel', 'Resort', 'Inn', 'Lodge', 'Suites'])}",
                description=fake.paragraph(nb_sentences=3),
                address=fake.street_address(),
                city=fake.city(),
                country=fake.country(),
                price_per_night=round(random.uniform(30, 500), 2),
                rating=round(random.uniform(2.5, 5.0), 1),
                amenities=generate_amenities(),
                room_type=random.choice(ROOM_TYPES),
                max_guests=random.randint(1, 8),
                available=random.choice([True, True, True, False])
            )
            accommodations.append(accommodation)

            if (i + 1) % 100 == 0:
                print(f"Generated {i + 1} records...")

        db.session.bulk_save_objects(accommodations)
        db.session.commit()
        print("Database seeded successfully with 1000 accommodations!")

if __name__ == '__main__':
    seed_database()
