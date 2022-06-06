#Générateur de cases pour intérieur de boîtes
## Présentation

Lors de l'utilisation de mon générateur de boîtes ([Lien Github](https://github.com/thierry7100/GenBox) , les cases générées (simples rangées et colonnes régulières) ne sont pas toujours adaptées au besoin.
Et pour couvrir tous les cas, le nombre de paramètres serait faramineux.
J'ai donc décidé de m'y prendre autrement. 

Avec cette extension, tout part d'un dessin (cela tombe bien, Inkscape est là pour cela). Donc il faut un dessin des cases que l'on souhaite réaliser. 
Attention ce dessin doit être uniquement composé de **rectangles** et les seules directions autorisées sont horizontales et verticales. Pas de cases avec des côtés non orthogonaux !

## Installation du logiciel

Il prend la forme d'un plugin inkscape. <br>
Pour l'installer, décompresser le .zip. Copier un des deux fichiers .inx (drawerbox.inx si vous préférez l'interface en anglais, drawerbox_fr.inx pour une interface en français) plus deux fichiers .py qui contiennent le code.  Copiez les 3 fichiers (un interface, extension.inx, et les deux programmes, extension .py) dans le répertoire d'extension inkscape. Pour connaître celui-ci, la commande Edition/Préférences vous indique le chemin, soit du répertoire global, soit celui pour vous seul utilisateur. Sous Linux c'est ~/.config/inkscape/extensions pour le répertoire local que j'utilise. Sous Windows,c'est dans C:\Users\Votre Nom Utilisateur\AppData\Roaming\inskscape\extensions.  <br>
Voir ci dessous pour le mode d'emploi du logiciel.

## Entrée du dessin

Je préconise de tout faire avec l'outil rectangle d'Inkscape (obligatoire dans cette version). Le mieux est de laisser le fond et de ne pas mettre de contours. Avec une épaisseur de bois de 3mm, dessiner des rectangles de 3 mm d'épaisseur. Dans cette première version, l'épaisseur est également demandée par l'extension Inkscape, les valeurs **DOIVENT** correspondre.

###Type de cases supportées
L'outil est capable de générer des connexions bord à bord entre des cloisons orthogonales. 

![c](/home/thierry/DrawerBox/Connection1.png  "Cloison bord à bord")

J'ai ici dessiné chaque cloison avec une couleur différente pour cet exemple, mais les couleurs n'ont aucune signification pour cette extension.
Il faut  ensuite correctement aligner les rectangles. Pour cela utiliser les fonctions d'Inkscape "aligner bord droit de l'objet au bord gauche de l'ancre" ou haut et bas... Pour que les jonctions soient reconnues le bord droit de la cloison horizontale doit coïncider avec le bord gauche de la cloison verticale (voud pouvez évidemment échanger droite et gauche et horizontal et vertical). Le programme arrondit toutes les coordonnés au dixième de mm, les valeurs arrondies **DOIVENT** correspondre 

Il est possible d'avoir des connexions à droite et à gauche (recouvrantes) sur une cloison. Les encoches sont prévues pour cela, au dessus à droite et en haut et en dessous a droite et en bas.

Il est également possible d'avoir des assemblages à mi bois avec des cloisons qui se croisent. 

![ ](/home/thierry/DrawerBox/Connection2.png  "cloison qui se croisent")

Dans ce cas, les cloisons doivent complètement traverser et "dépasser" d'au moins 0.1mm (arrondi du programme). Sinon, il n'y aura pas de jonction tracée puisque la connexion ne sera ni bord à bord ni traversante ! 

Vous pouvez également avoir des cloisons qui ne se touchent pas, dans ce cas il n'y aura pas d'attaches sur les côtés.

Voici un exemple un peu plus complexe

![ ](/home/thierry/DrawerBox/example.png  "Exemple pour intérieur de boîte")

Ici encore, les couleurs sont juste là pour identifier les différentes cloisons.

## Utilisation de l'extension

Une fois le dessin réalisé, sélectionnez le entièrement. Seuls les rectangles sélectionnés seront traités.
Puis dans les extensions d'Inkscape choisissez "fablab/générateur de cases pour boîte". La boîte de dialogue suivante doit apparaître.

![ ](/home/thierry/DrawerBox/Dialog.png  "Dialogue de l'extension")

Pour unité, choisissez votre unité habituelle (mm généralement).
Ensuite définissez l'épaisseur du matériau (ici 3mm).
Puis la hauteur des cases.

La valeur de compensation du faisceau laser est destinée à compenser l'épaisseur du faisceau pour obtenir des emboîtements assez durs, qui peuvent tenir sans colle (au moins provisoirement). 0.1 mm est une bonne valeur pour le bois fin. Pour d'autres matériaux c'est à ajuster.

Enfin, vous pouvez choisir ou non de dessiner un fond sur votre structure. Je conseille de le faire, cela renforce considérablement la réalisation, mais si vous êtes juste en hauteur...

## Assemblage

Même pour une réalisation simple, vous vous retrouvez avec un certains nombre de morceaux, il faut donc faire attention pour l'assemblage !
Je conseille d'avoir le plan sous les yeux  !

Il me semble préférable de commencer par l'intérieur de la boîte, suivant 
la taille des pièces, cela peut être un peu difficile à assembler.
Si vous avez des assemblages à mi bois, insérer d'abord les pièce "du bas" puis celles du dessus. Ce type d'assemblage est généralement plus simple à assembler que ceux bord à bord.

Voici réalisé le dessin ci-dessus

![ ](/home/thierry/DrawerBox/DrawerBox1.jpg  "Intérieur monté")


## Évolutions possibles

A vous de me dire, ou à faire vous même...
Dans ce cas, n'oubliez pas de republier !

