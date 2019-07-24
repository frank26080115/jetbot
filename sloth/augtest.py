import dataset
import augmentation

def augmentation_generate(dpath):
	x = dataset.ImageSet()
	x.load_dir(dpath)
	x.augment_all(augmentation.get_random_augs(2), transform = True)

augmentation_generate("C:\\Users\\frank\\Pictures\\testset")

