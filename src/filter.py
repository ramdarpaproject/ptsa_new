from scipy.signal import butter
from numpy import asarray

def buttfilt(dat,freqRange,sampleRate,filtType,order):
    """Wrapper for a Butterworth filter.

    """
    
    # make sure dat is an array
    dat = asarray(dat)

    # see if data has more than one dimension
    if len(dat.shape) > 1:
        # has more dimensions, loop over first dimension
        filtDat = []
        for i in xrange(dat.shape[0]):
            filtDat.append(buttfilt(dat[i],freqRange,sampleRate,filtType,order))

        # turn into array
        filtDat = asarray(filtDat)
    else:
        # is single dimension, so filter it
        # make the freqRange an array
        freqRange = asarray(freqRange)

        # Nyquist frequency
        nyq=sampleRate/2.;

        # generate the butterworth filter coefficients
        [b,a]=butter(order,freqRange/nyq,filtType)

        # run the filter on 
        filtDat=filtfilt(b,a,dat)

    return filtDat

######
# Code for decimate from http://www.bigbold.com/snippets/posts/show/1209
######

from scipy.signal import cheby1, firwin, lfilter

def decimate(x, q, n=None, ftype='iir', axis=-1):
    """downsample the signal x by an integer factor q, using an order n filter
    
    By default, an order 8 Chebyshev type I filter is used or a 30 point FIR 
    filter with hamming window if ftype is 'fir'.

    (port to python of the GNU Octave function decimate.)

    Inputs:
        x -- the signal to be downsampled (N-dimensional array)
        q -- the downsampling factor
        n -- order of the filter (1 less than the length of the filter for a
             'fir' filter)
        ftype -- type of the filter; can be 'iir' or 'fir'
        axis -- the axis along which the filter should be applied
    
    Outputs:
        y -- the downsampled signal

    """

    if type(q) != type(1):
        raise TypeError, "q should be an integer"

    if n is None:
        if ftype == 'fir':
            n = 30
        else:
            n = 8
    if ftype == 'fir':
        b = firwin(n+1, 1./q, window='hamming')
        y = lfilter(b, 1., x, axis=axis)
    else:
        (b, a) = cheby1(n, 0.05, 0.8/q)

        y = lfilter(b, a, x, axis=axis)

    return y.swapaxes(0,axis)[::q].swapaxes(0,axis)


############
# Code for filtfilt from http://www.scipy.org/Cookbook/FiltFilt
############

from numpy import vstack, hstack, eye, ones, zeros, linalg, \
newaxis, r_, flipud, convolve, matrix
from scipy.signal import lfilter

def lfilter_zi(b,a):
    #compute the zi state from the filter parameters. see [Gust96].

    #Based on:
    # [Gust96] Fredrik Gustafsson, Determining the initial states in forward-backward 
    # filtering, IEEE Transactions on Signal Processing, pp. 988--992, April 1996, 
    # Volume 44, Issue 4

    n=max(len(a),len(b))

    zin = (  eye(n-1) - hstack( (-a[1:n,newaxis],
                                 vstack((eye(n-2), zeros(n-2))))))

    zid=  b[1:n] - a[1:n]*b[0]

    zi_matrix=linalg.inv(zin)*(matrix(zid).transpose())
    zi_return=[]

    #convert the result into a regular array (not a matrix)
    for i in range(len(zi_matrix)):
      zi_return.append(float(zi_matrix[i][0]))

    return zi_return




def filtfilt(b,a,x):
    #For now only accepting 1d arrays
    ntaps=max(len(a),len(b))
    edge=ntaps*3

    if x.ndim != 1:
        raise ValueError, "Filiflit is only accepting 1 dimension arrays."

    #x must be bigger than edge
    if x.size < edge:
        raise ValueError, "Input vector needs to be bigger than 3 * max(len(a),len(b)."


    if len(a)!=len(b):
        b=r_[b,zeros(len(a)-len(b))]


    zi=lfilter_zi(b,a)

    #Grow the signal to have edges for stabilizing 
    #the filter with inverted replicas of the signal
    s=r_[2*x[0]-x[edge:1:-1],x,2*x[-1]-x[-1:-edge:-1]]
    #in the case of one go we only need one of the extrems 
    # both are needed for filtfilt

    for i in range(len(zi)):
      zi[i]=zi[i]*s[0]


    (y,zf)=lfilter(b,a,s,-1,zi)

    for i in range(len(zi)):
      zi[i]=zi[i]*y[-1]

    (y,zf)=lfilter(b,a,flipud(y),-1,zi)

    return flipud(y[edge-1:-edge+1])



# if __name__=='__main__':

#     from scipy.signal import butter
#     from scipy import sin, arange, pi, randn

#     from pylab import plot, legend, show, hold

#     t=arange(-1,1,.01)
#     x=sin(2*pi*t*.5+2)
#     #xn=x + sin(2*pi*t*10)*.1
#     xn=x+randn(len(t))*0.05

#     [b,a]=butter(3,0.05)

#     z=lfilter(b,a,xn)
#     y=filtfilt(b,a,xn)



#     plot(x,'c')
#     hold(True)
#     plot(xn,'k')
#     plot(z,'r')
#     plot(y,'g')

#     legend(('original','noisy signal','lfilter - butter 3 order','filtfilt - butter 3 order'))
#     hold(False)
#     show()