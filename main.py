class Voiture:
    def __init__(self, marque, modele, annee, immat, dispo=True):
        self.marque = marque
        self.modele = modele
        self.annee = annee
        self.immat = immat
        self.dispo = dispo
    
    def est_disponible(self):
        return self.dispo
    
    def afficher_details(self):
        print(f"Marque: {self.marque}")
        print(f"Modèle: {self.modele}")
        print(f"Année: {self.annee}")
        print(f"Immatriculation: {self.immat}")
        print(f"Disponible: {'Oui' if self.dispo else 'Non'}")

class Agence:
    def __init__ (self):
        self.voitures = []

    def ajouter_voiture(self, voiture):
        self.voitures.append(voiture)
        print(f"Voiture {voiture.marque} {voiture.modele} ajoutée à l'agence.")
    
    def louer_voiture(self, immat):
        for voiture in self.voitures:
            if voiture.immat == immat:
                if voiture.est_disponible():
                    voiture.dispo = False
                    print(f"Voiture {voiture.marque} {voiture.modele} louée avec succès.")
                    return
                else:
                    print(f"Voiture {voiture.marque} {voiture.modele} n'est pas disponible.")
                    return
        print("Voiture non trouvée.")
    
    def retourner_voiture(self, immat):
        for voiture in self.voitures:
            if voiture.immat == immat:
                if not voiture.est_disponible():
                    voiture.dispo = True
                    print(f"Voiture {voiture.marque} {voiture.modele} retournée avec succès.")
                    return
                else:
                    print(f"Voiture {voiture.marque} {voiture.modele} n'était pas louée.")
                    return
        print("Voiture non trouvée.")

    def afficher_voitures_disponibles(self):
        print("Voitures disponibles:")
        for voiture in self.voitures:
            if voiture.est_disponible():
                voiture.afficher_details()
                print()
    
    def supprimer_voiture(self, immat):
        for i, voiture in enumerate(self.voitures):
            if voiture.immat == immat:
                del self.voitures[i]
                print(f"Voiture {voiture.marque} {voiture.modele} supprimée de l'agence.")
                return
        print("Voiture non trouvée.")
    
if __name__ == "__main__":

    v1 = Voiture("Renault", "Clio",  2021, "AB-123-CD")
    v2 = Voiture("Peugeot", "308",   2022, "XY-456-ZT")
    v3 = Voiture("Toyota",  "Yaris", 2023, "GH-789-IJ")

    agence = Agence()
    agence.ajouter_voiture(v1)
    agence.ajouter_voiture(v2)
    agence.ajouter_voiture(v3)

    agence.afficher_voitures_disponibles()

    agence.louer_voiture("AB-123-CD")

    agence.supprimer_voiture("XY-456-ZT") 

    agence.afficher_voitures_disponibles()
    