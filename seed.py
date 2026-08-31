"""Seed the professions catalogue and demo accounts. Run inside the backend container:
    python seed.py
"""
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.profession import Profession
from app.models.professional import ProfessionalProfile
from app.models.service import ProfessionalService
from app.models.user import User, UserRole

PROFESSIONS = [
    ("Plombier", "plombier", "wrench", "Batiment"),
    ("Electricien", "electricien", "bolt", "Batiment"),
    ("Menuisier", "menuisier", "hammer", "Batiment"),
    ("Peintre", "peintre", "paint-roller", "Batiment"),
    ("Macon", "macon", "trowel", "Batiment"),
    ("Serrurier", "serrurier", "key", "Batiment"),
    ("Jardinier", "jardinier", "leaf", "Exterieur"),
    ("Menage", "menage", "broom", "Maison"),
    ("Pressing", "pressing", "shirt", "Maison"),
    ("Demenageur", "demenageur", "truck", "Maison"),
    ("Coiffeur a domicile", "coiffeur-a-domicile", "scissors", "Beaute"),
    ("Cours particuliers", "cours-particuliers", "book", "Education"),
    ("Reparation informatique", "reparation-informatique", "laptop", "Tech"),
    ("Photographe", "photographe", "camera", "Evenementiel"),
    ("Traiteur", "traiteur", "utensils", "Evenementiel"),
]

CLIENT_PASSWORD = "Client123!"
PRO_PASSWORD = "Pro123456!"

CLIENTS = [
    ("Aicha Kone", "client1@artisanconnect.demo", "+2250700000001"),
    ("Moussa Diarra", "client2@artisanconnect.demo", "+2250700000002"),
    ("Fatou Bamba", "client3@artisanconnect.demo", "+2250700000003"),
]

PROFESSIONALS = [
    dict(
        full_name="Kouassi Yao",
        email="plombier.demo@artisanconnect.demo",
        phone="+2250700000010",
        profession_slug="plombier",
        business_name="Kouassi Plomberie Express",
        description="Plombier experimente, interventions rapides a domicile.",
        address="Cocody",
        city="Abidjan",
        latitude=5.3600,
        longitude=-4.0083,
        services=[
            ("Changement de robinet", "intervention", 3000),
            ("Debouchage de tuyau", "intervention", 1000),
            ("Installation chauffe-eau", "intervention", 15000),
        ],
    ),
    dict(
        full_name="Jean-Baptiste N'Guessan",
        email="electricien.demo@artisanconnect.demo",
        phone="+2250700000011",
        profession_slug="electricien",
        business_name="JB Electricite",
        description="Installation et depannage electrique, particuliers et bureaux.",
        address="Marcory",
        city="Abidjan",
        latitude=5.3450,
        longitude=-3.9950,
        services=[
            ("Changement de prise", "intervention", 2000),
            ("Installation disjoncteur", "intervention", 8000),
            ("Recherche de panne", "intervention", 5000),
        ],
    ),
    dict(
        full_name="Adama Traore",
        email="menuisier.demo@artisanconnect.demo",
        phone="+2250700000012",
        profession_slug="menuisier",
        business_name="Adama Menuiserie",
        description="Fabrication et reparation de meubles sur mesure.",
        address="Yopougon",
        city="Abidjan",
        latitude=5.3700,
        longitude=-4.0200,
        services=[
            ("Reparation de porte", "intervention", 5000),
            ("Fabrication etagere", "piece", 20000),
        ],
    ),
    dict(
        full_name="Aminata Cisse",
        email="pressing.demo@artisanconnect.demo",
        phone="+2250700000013",
        profession_slug="pressing",
        business_name="Pressing Aminata",
        description="Nettoyage et repassage rapide, remise en main propre.",
        address="Plateau",
        city="Abidjan",
        latitude=5.3550,
        longitude=-4.0100,
        services=[
            ("1 vetement", "vetement", 500),
            ("5 vetements", "lot", 2000),
            ("Nettoyage costume", "piece", 3000),
        ],
    ),
    dict(
        full_name="Mariam Coulibaly",
        email="menage.demo@artisanconnect.demo",
        phone="+2250700000014",
        profession_slug="menage",
        business_name="Mariam Services Menagers",
        description="Menage soigneux pour appartements et maisons.",
        address="Riviera",
        city="Abidjan",
        latitude=5.3800,
        longitude=-3.9900,
        services=[
            ("Menage forfait 2h", "forfait", 10000),
            ("Grand menage journee", "forfait", 25000),
        ],
    ),
    dict(
        full_name="Ibrahim Ouattara",
        email="coiffeur.demo@artisanconnect.demo",
        phone="+2250700000015",
        profession_slug="coiffeur-a-domicile",
        business_name="Ibrahim Coiffure a Domicile",
        description="Coiffeur a domicile, hommes et femmes.",
        address="Treichville",
        city="Abidjan",
        latitude=5.3400,
        longitude=-4.0300,
        services=[
            ("Coupe homme", "prestation", 3000),
            ("Coiffure femme", "prestation", 8000),
        ],
    ),
]


def seed_professions(db):
    for name, slug, icon, category in PROFESSIONS:
        if db.query(Profession).filter(Profession.slug == slug).first():
            continue
        db.add(Profession(name=name, slug=slug, icon=icon, category=category))
    db.commit()
    print(f"Seeded {len(PROFESSIONS)} professions (skipping existing).")


def seed_clients(db):
    created = 0
    for full_name, email, phone in CLIENTS:
        if db.query(User).filter(User.email == email).first():
            continue
        db.add(
            User(
                email=email,
                phone=phone,
                full_name=full_name,
                role=UserRole.CLIENT,
                hashed_password=hash_password(CLIENT_PASSWORD),
            )
        )
        created += 1
    db.commit()
    print(f"Seeded {created} demo client accounts (skipping existing).")


def seed_professionals(db):
    created = 0
    for pro in PROFESSIONALS:
        if db.query(User).filter(User.email == pro["email"]).first():
            continue
        profession = db.query(Profession).filter(Profession.slug == pro["profession_slug"]).first()
        if not profession:
            continue

        user = User(
            email=pro["email"],
            phone=pro["phone"],
            full_name=pro["full_name"],
            role=UserRole.PROFESSIONAL,
            hashed_password=hash_password(PRO_PASSWORD),
        )
        db.add(user)
        db.flush()

        profile = ProfessionalProfile(
            user_id=user.id,
            profession_id=profession.id,
            business_name=pro["business_name"],
            description=pro.get("description"),
            address=pro.get("address"),
            city=pro.get("city"),
            latitude=pro["latitude"],
            longitude=pro["longitude"],
        )
        db.add(profile)
        db.flush()

        for position, (name, unit, price) in enumerate(pro["services"]):
            db.add(
                ProfessionalService(
                    professional_id=profile.id,
                    name=name,
                    unit=unit,
                    price=price,
                    currency="FCFA",
                    position=position,
                )
            )
        created += 1
    db.commit()
    print(f"Seeded {created} demo professional accounts (skipping existing).")


def run():
    db = SessionLocal()
    try:
        seed_professions(db)
        seed_clients(db)
        seed_professionals(db)
    finally:
        db.close()


if __name__ == "__main__":
    run()
