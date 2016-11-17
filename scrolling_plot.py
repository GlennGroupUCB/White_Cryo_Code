import matplotlib.pyplot as plt
import numpy as np
import time


lines = ['-','--','-.']
labels = ['4K P.T','ADR baseplate','50K P.T.','50K plate','ADR rad shield','4He pump','3He pump','4He switch','3He switch','ADR switch','4K-1K switch','4K plate','3He head','4He head','Top of 4K H.S.']
colors = ['b','g','r','c','m','y','k','w']

#plots = (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14)
plots = (0,1,2,3,5,6,7,8,9,10,11,12,13,14)

start = time.time()
plt.figure(1,figsize = (19,8))
x = np.arange(-100,0)*1.
y = np.ones((100,15))*-1
plt.title("Thermometry")
plt.xlabel("time (mins)")
plt.ylabel("Temperature (K)")
plt.ion()
plt.show()


i = 0

try:
    while True:
        t = time.time() - start
        x = np.roll(x,-1)
        y = np.roll(y,-1,axis = 0)
        x[99] = t/1.
        print(t,i)
        plt.xlim(x[0],x[99])
        plt.ylim(0.1,1000)
        for j in plots:
            y[99,j] = 300.*np.exp(-i/10.)+0.1+5.*j
            plt.semilogy(x,y[:,j],color = colors[np.mod(j,8)],linestyle = lines[j/7],linewidth = 2, label = labels[j])
        if i == 0:
            plt.legend(ncol = 7,loc =2)
        plt.draw()
        time.sleep(1)
        i = i+1

except KeyboardInterrupt:
    pass

print("finished")
        
