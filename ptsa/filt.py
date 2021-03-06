#emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See the COPYING file distributed along with the PTSA package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

from scipy.signal import butter, cheby1, firwin, lfilter
from numpy import asarray, vstack, hstack, eye, ones, zeros, linalg, newaxis, r_, flipud, convolve, matrix, array,concatenate
import numpy as np
from scipy.special import sinc


from .helper import reshape_to_2d, reshape_from_2d, repeat_to_match_dims

from .filtfilt import filtfilt as filtfilt_future

import pdb

def buttfilt(dat,freq_range,sample_rate,filt_type,order,axis=-1):
    """Wrapper for a Butterworth filter.

    """

    # make sure dat is an array
    dat = asarray(dat)

    # reshape the data to 2D with time on the 2nd dimension
    #origshape = dat.shape
    #dat = reshape_to_2d(dat,axis)

    # set up the filter
    freq_range = asarray(freq_range)

    # Nyquist frequency
    nyq=sample_rate/2.;

    # generate the butterworth filter coefficients
    [b,a]=butter(order,freq_range/nyq,filt_type)

    # loop over final dimension
    #for i in range(dat.shape[0]):
    #    dat[i] = filtfilt(b,a,dat[i])
    #dat = filtfilt2(b,a,dat,axis=axis)
    dat = filtfilt_future(b,a,dat,axis=axis)

    # reshape the data back
    #dat = reshape_from_2d(dat,axis,origshape)
    return dat

######
# Code for decimate modified from http://www.bigbold.com/snippets/posts/show/1209
######

# from scipy.signal import cheby1, firwin, lfilter
# this import is now at the top of the file 

def decimate(x, q, n=None, ftype='iir', axis=-1):
    """Downsample the signal x by an integer factor q, using an order n filter

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
        raise TypeError("q should be an integer")

    if n is None:
        if ftype == 'fir':
            n = 30
        else:
            n = 8
    if ftype == 'fir':
        # PBS - This method must be verified
        b = firwin(n+1, 1./q, window='hamming')
        y = lfilter(b, 1., x, axis=axis)
    else:
        (b, a) = cheby1(n, 0.05, 0.8/q)

        # reshape the data to 2D with time on the 2nd dimension
        origshape = x.shape
        y = reshape_to_2d(x,axis)

        # loop over final dimension
        for i in range(y.shape[0]):
            y[i] = filtfilt(b,a,y[i])
        #y = filtfilt2(b,a,y)

        # reshape the data back
        y = reshape_from_2d(y,axis,origshape)

        # This needs to be filtfilt eventually
        #y = lfilter(b, a, x, axis=axis)

    return y.swapaxes(0,axis)[::q].swapaxes(0,axis)


############
# Code for filtfilt from http://www.scipy.org/Cookbook/FiltFilt
############

# from numpy import vstack, hstack, eye, ones, zeros, linalg, \
# newaxis, r_, flipud, convolve, matrix
# from scipy.signal import lfilter
# imports now at top of file

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

    return array(zi_return)

def filtfilt(b,a,x):
    #For now only accepting 1d arrays
    ntaps=max(len(a),len(b))
    edge=ntaps*3

    if x.ndim != 1:
        raise ValueError("Filtflit is only accepting 1 dimension arrays.")

    #x must be bigger than edge
    if x.size < edge:
        raise ValueError("Input vector needs to be bigger than 3 * max(len(a),len(b).")


    if len(a)!=len(b):
        b=r_[b,zeros(len(a)-len(b))]


    zi=lfilter_zi(b,a)

    #Grow the signal to have edges for stabilizing 
    #the filter with inverted replicas of the signal
    s=r_[2*x[0]-x[edge:1:-1],x,2*x[-1]-x[-1:-edge:-1]]
    #in the case of one go we only need one of the extrems 
    # both are needed for filtfilt

    (y,zf)=lfilter(b,a,s,-1,zi*s[0])

    (y,zf)=lfilter(b,a,flipud(y),-1,zi*y[-1])

    return flipud(y[edge-1:-edge+1])



def filtfilt2(b,a,x,axis=-1):
    # trying to accept N-dimensional arrays

    # calculate the edge needed
    ntaps=max(len(a),len(b))
    edge=ntaps*3

    #x must be bigger than edge
    if x.shape[axis] < edge:
        raise ValueError("Input vector needs to be bigger than 3 * max(len(a),len(b).")

    # fill out b if necessary
    if len(a)!=len(b):
        b=r_[b,zeros(len(a)-len(b))]

    # calculate the initial conditions scaling factor
    zi=lfilter_zi(b,a)

    #Grow the signal to have edges for stabilizing 
    #the filter with inverted replicas of the signal
    #s=r_[2*x[0]-x[edge:1:-1],x,2*x[-1]-x[-1:-edge:-1]]

    bRange = range(edge,1,-1)
    sBeg = 2*x.take([0],axis).repeat(len(bRange),axis) - x.take(bRange,axis)
    eRange = range(-1,-edge,-1)
    sEnd = 2*x.take([-1],axis).repeat(len(eRange),axis) - x.take(eRange,axis)

    s = concatenate((sBeg,x,sEnd),axis)

    #in the case of one go we only need one of the extremes 
    # both are needed for filtfilt

    # peform filter in forward direction
    sBeg = s.take([0],axis).repeat(len(zi),axis)
    ziBeg = repeat_to_match_dims(zi,sBeg,axis) * sBeg
    (y,zf)=lfilter(b,a,s,axis,ziBeg)

    # perform filter in reverse direction
    sEnd = y.take([-1],axis).repeat(len(zi),axis)
    ziEnd = repeat_to_match_dims(zi,sEnd,axis) * sEnd
    (y,zf)=lfilter(b,a,y.take(range(y.shape[axis]-1,-1,-1),axis),axis,ziEnd)

    # flip it back
    y = y.take(range(y.shape[axis]-1,-1,-1),axis)
    return y.take(range(edge-1,y.shape[axis]-edge+1),axis)


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


# from http://mail.scipy.org/pipermail/scipy-user/2009-November/023101.html
def firls(N, f, D=None):
    """Least-squares FIR filter.
    N -- filter length, must be odd
    f -- list of tuples of band edges
       Units of band edges are Hz with 0.5 Hz == Nyquist
       and assumed 1 Hz sampling frequency
    D -- list of desired responses, one per band
    """
    if D is None:
        D = [1, 0]
    assert len(D) == len(f), "must have one desired response per band"
    assert N%2 == 1, 'filter length must be odd'
    L = (N-1)//2

    k = np.arange(L+1)
    k.shape = (1, L+1)
    j = k.T

    R = 0
    r = 0
    for i, (f0, f1) in enumerate(f):
        R += np.pi*f1*sinc(2*(j-k)*f1) - np.pi*f0*sinc(2*(j-k)*f0) + \
             np.pi*f1*sinc(2*(j+k)*f1) - np.pi*f0*sinc(2*(j+k)*f0)

        r += D[i]*(2*np.pi*f1*sinc(2*j*f1) - 2*np.pi*f0*sinc(2*j*f0))

    a = np.dot(np.linalg.inv(R), r)
    a.shape = (-1,)
    h = np.zeros(N)
    h[:L] = a[:0:-1]/2.
    h[L] = a[0]
    h[L+1:] = a[1:]/2.
    return h

