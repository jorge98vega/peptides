from matplotlib import pyplot as plt
import numpy as np

folder = "output"

data = np.genfromtxt(folder + "/energias_resres.dat")

z = data[:,7]
zmatrix=np.reshape(z, (160, 160))

zcut=zmatrix[80:,:80]
x=np.linspace(1, 80, num=80)
y=np.linspace(81, 160, num=80)

plt.pcolormesh(x,y,zcut,vmin=-0.2,vmax=0.2,cmap='bwr')
plt.savefig(folder + "/mapbig.png")
plt.clf()

# zcut2=zmatrix[980:,399:599]
# x2=np.linspace(401, 600, num=200)

# plt.pcolormesh(x2,y,zcut2,vmin=-2,vmax=2,cmap='bwr')
# plt.savefig('mapzoom.png')

