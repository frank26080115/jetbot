import dataset

def augmentation_generate(dpath):
	x = dataset.ImageSet()
	x.load_dir(dpath)
	x.augment_all(["c"], transform = False)

augmentation_generate("C:\\Users\\frank\\Pictures\\testset")

