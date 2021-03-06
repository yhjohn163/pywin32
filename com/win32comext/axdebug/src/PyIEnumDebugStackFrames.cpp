// This file implements the IEnumDebugStackFrames Interface and Gateway for Python.
// Generated by makegw.py

#include "stdafx.h"
#include "PythonCOM.h"
#include "PythonCOMServer.h"
#include "PyIEnumDebugStackFrames.h"

// @doc - This file contains autoduck documentation

// ---------------------------------------------------
//
// Interface Implementation

PyIEnumDebugStackFrames::PyIEnumDebugStackFrames(IUnknown *pdisp):
	PyIUnknown(pdisp)
{
	ob_type = &type;
}

PyIEnumDebugStackFrames::~PyIEnumDebugStackFrames()
{
}

/* static */ IEnumDebugStackFrames *PyIEnumDebugStackFrames::GetI(PyObject *self)
{
	return (IEnumDebugStackFrames *)PyIUnknown::GetI(self);
}

// @pymethod object|PyIEnumDebugStackFrames|Next|Retrieves a specified number of items in the enumeration sequence.
PyObject *PyIEnumDebugStackFrames::Next(PyObject *self, PyObject *args)
{
	long celt = 1;
	// @pyparm int|num|1|Number of items to retrieve.
	if ( !PyArg_ParseTuple(args, "|l:Next", &celt) )
		return NULL;

	IEnumDebugStackFrames *pIEDebugStackFrames = GetI(self);
	if ( pIEDebugStackFrames == NULL )
		return NULL;

	DebugStackFrameDescriptor *rgVar = new DebugStackFrameDescriptor [celt];
	if ( rgVar == NULL ) {
		PyErr_SetString(PyExc_MemoryError, "allocating result IDebugStackFrameDescriptor");
		return NULL;
	}

	int i;
/*	for ( i = celt; i--; )
		// *** possibly init each structure element???
*/

	ULONG celtFetched = 0;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIEDebugStackFrames->Next(celt, rgVar, &celtFetched);
	PY_INTERFACE_POSTCALL;
	if (  HRESULT_CODE(hr) != ERROR_NO_MORE_ITEMS && FAILED(hr) )
	{
		delete [] rgVar;
		return SetPythonCOMError(self,hr);
	}

	PyObject *result = PyTuple_New(celtFetched);
	if ( result != NULL )
	{
		for ( i = celtFetched; i--; )
		{
			// Make a result tuple.
			PyObject *obFrame = PyCom_PyObjectFromIUnknown(rgVar[i].pdsf, IID_IDebugStackFrame, FALSE);
			rgVar[i].pdsf = NULL;
			if ( obFrame == NULL)
			{
				Py_DECREF(result);
				result = NULL;
				break;
			}
			PyObject *obUnkFinal = PyCom_PyObjectFromIUnknown(rgVar[i].punkFinal, IID_IUnknown, TRUE);
			PyTuple_SET_ITEM(result, i, Py_BuildValue("OiiiO", obFrame, rgVar[i].dwMin, rgVar[i].dwLim, rgVar[i].fFinal, obUnkFinal));
			Py_DECREF(obFrame);
			Py_XDECREF(obUnkFinal);
		}
	}
	for ( i = celtFetched; i--; ) PYCOM_RELEASE(rgVar[i].pdsf);
	delete [] rgVar;
	return result;
}

// @pymethod |PyIEnumDebugStackFrames|Skip|Skips over the next specified elementes.
PyObject *PyIEnumDebugStackFrames::Skip(PyObject *self, PyObject *args)
{
	long celt;
	if ( !PyArg_ParseTuple(args, "l:Skip", &celt) )
		return NULL;

	IEnumDebugStackFrames *pIEDebugStackFrames = GetI(self);
	if ( pIEDebugStackFrames == NULL )
		return NULL;

	PY_INTERFACE_PRECALL;
	HRESULT hr = pIEDebugStackFrames->Skip(celt);
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return SetPythonCOMError(self,hr);

	Py_INCREF(Py_None);
	return Py_None;
}

// @pymethod |PyIEnumDebugStackFrames|Reset|Resets the enumeration sequence to the beginning.
PyObject *PyIEnumDebugStackFrames::Reset(PyObject *self, PyObject *args)
{
	if ( !PyArg_ParseTuple(args, ":Reset") )
		return NULL;

	IEnumDebugStackFrames *pIEDebugStackFrames = GetI(self);
	if ( pIEDebugStackFrames == NULL )
		return NULL;

	PY_INTERFACE_PRECALL;
	HRESULT hr = pIEDebugStackFrames->Reset();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return SetPythonCOMError(self,hr);

	Py_INCREF(Py_None);
	return Py_None;
}

// @pymethod <o PyIEnumDebugStackFrames>|PyIEnumDebugStackFrames|Clone|Creates another enumerator that contains the same enumeration state as the current one
PyObject *PyIEnumDebugStackFrames::Clone(PyObject *self, PyObject *args)
{
	if ( !PyArg_ParseTuple(args, ":Clone") )
		return NULL;

	IEnumDebugStackFrames *pIEDebugStackFrames = GetI(self);
	if ( pIEDebugStackFrames == NULL )
		return NULL;

	IEnumDebugStackFrames *pClone;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIEDebugStackFrames->Clone(&pClone);
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return SetPythonCOMError(self,hr);

	return PyCom_PyObjectFromIUnknown(pClone, IID_IEnumDebugStackFrames, FALSE);
}

// @object PyIEnumDebugStackFrames|A Python interface to IEnumDebugStackFrames
static struct PyMethodDef PyIEnumDebugStackFrames_methods[] =
{
	{ "Next", PyIEnumDebugStackFrames::Next, 1 },    // @pymeth Next|Retrieves a specified number of items in the enumeration sequence.
	{ "Skip", PyIEnumDebugStackFrames::Skip, 1 },	// @pymeth Skip|Skips over the next specified elementes.
	{ "Reset", PyIEnumDebugStackFrames::Reset, 1 },	// @pymeth Reset|Resets the enumeration sequence to the beginning.
	{ "Clone", PyIEnumDebugStackFrames::Clone, 1 },	// @pymeth Clone|Creates another enumerator that contains the same enumeration state as the current one.
	{ NULL }
};

PyComTypeObject PyIEnumDebugStackFrames::type("PyIEnumDebugStackFrames",
		&PyIUnknown::type,
		sizeof(PyIEnumDebugStackFrames),
		PyIEnumDebugStackFrames_methods,
		GET_PYCOM_CTOR(PyIEnumDebugStackFrames));

// ---------------------------------------------------
//
// Gateway Implementation

STDMETHODIMP PyGEnumDebugStackFrames::Next( 
            /* [in] */ ULONG celt,
            /* [length_is][size_is][out] */ DebugStackFrameDescriptor __RPC_FAR *rgVar,
            /* [out] */ ULONG __RPC_FAR *pCeltFetched)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	Py_ssize_t len;
	HRESULT hr = InvokeViaPolicy("Next", &result, "i", celt);
	if ( FAILED(hr) )
		return hr;

	if ( !PySequence_Check(result) )
		goto error;
	len = PyObject_Length(result);
	if ( len == -1 )
		goto error;
	if ( len > (Py_ssize_t)celt)
		len = celt;

	if ( pCeltFetched )
		*pCeltFetched = PyWin_SAFE_DOWNCAST(len, Py_ssize_t, ULONG);

	Py_ssize_t i;
	for ( i = 0; i < len; ++i )
	{
		PyObject *ob = PySequence_GetItem(result, i);
		if ( ob == NULL )
			goto error;
		if (!PyTuple_Check(ob)) {
			Py_DECREF(ob);
			PyErr_SetString(PyExc_TypeError, "PyIEnumDebugStackFrames::Next must return a tuple.");
			goto error;
		}
		PyObject *obEnum, *obUnk;
		if (!PyArg_ParseTuple(ob, "OiiiO", &obEnum, &rgVar[i].dwMin, &rgVar[i].dwLim, &rgVar[i].fFinal, &obUnk)) {
			Py_DECREF(ob);
			goto error;
		}

		if ( !PyCom_InterfaceFromPyInstanceOrObject(obEnum, IID_IDebugStackFrame, (void **)&rgVar[i].pdsf, FALSE) ||
		     !PyCom_InterfaceFromPyInstanceOrObject(obUnk, IID_IUnknown, (void **)&rgVar[i].punkFinal, TRUE) )
		{
			Py_DECREF(ob);
			Py_DECREF(result);
			return PyCom_SetCOMErrorFromPyException(IID_IEnumDebugStackFrames);
		}
		Py_DECREF(ob);
	}

	Py_DECREF(result);

	return len < (Py_ssize_t)celt ? S_FALSE : S_OK;

  error:
	hr = PyErr_Occurred() ? PyCom_SetCOMErrorFromPyException(IID_IEnumDebugStackFrames)
		                          : PyCom_SetCOMErrorFromSimple(E_FAIL, IID_IEnumDebugStackFrames);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGEnumDebugStackFrames::Skip( 
            /* [in] */ ULONG celt)
{
	PY_GATEWAY_METHOD;
	return InvokeViaPolicy("Skip", NULL, "i", celt);
}

STDMETHODIMP PyGEnumDebugStackFrames::Reset(void)
{
	PY_GATEWAY_METHOD;
	return InvokeViaPolicy("Reset");
}

STDMETHODIMP PyGEnumDebugStackFrames::Clone( 
            /* [out] */ IEnumDebugStackFrames __RPC_FAR *__RPC_FAR *ppEnum)
{
	PY_GATEWAY_METHOD;
	PyObject * result;
	HRESULT hr = InvokeViaPolicy("Clone", &result);
	if ( FAILED(hr) )
		return hr;

	/*
	** Make sure we have the right kind of object: we should have some kind
	** of IUnknown subclass wrapped into a PyIUnknown instance.
	*/
	if ( !PyIBase::is_object(result, &PyIUnknown::type) )
	{
		/* the wrong kind of object was returned to us */
		Py_DECREF(result);
		return PyCom_SetCOMErrorFromSimple(E_FAIL, IID_IEnumDebugStackFrames);
	}

	/*
	** Get the IUnknown out of the thing. note that the Python ob maintains
	** a reference, so we don't have to explicitly AddRef() here.
	*/
	IUnknown *punk = ((PyIUnknown *)result)->m_obj;
	if ( !punk )
	{
		/* damn. the object was released. */
		Py_DECREF(result);
		return PyCom_SetCOMErrorFromSimple(E_FAIL, IID_IEnumDebugStackFrames);
	}

	/*
	** Get the interface we want. note it is returned with a refcount.
	** This QI is actually going to instantiate a PyGEnumDebugStackFrames.
	*/
	Py_BEGIN_ALLOW_THREADS
	hr = punk->QueryInterface(IID_IEnumDebugStackFrames, (LPVOID *)ppEnum);
	Py_END_ALLOW_THREADS

	/* done with the result; this DECREF is also for <punk> */
	Py_DECREF(result);

	return PyCom_SetCOMErrorFromSimple(hr, IID_IEnumDebugStackFrames);
}
