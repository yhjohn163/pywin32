"""Support for dynamic COM client support.

Introduction
 Dynamic COM client support is the ability to use a COM server without
 prior knowledge of the server.  This can be used to talk to almost all
 COM servers, including much of MS Office.
 
 In general, you should not use this module directly - see below.
 
Example
 >>> import win32com.client
 >>> xl = win32com.client.Dispatch("Excel.Application")
 # The line above invokes the functionality of this class.
 # xl is now an object we can use to talk to Excel.
 >>> xl.Visible = 1 # The Excel window becomes visible.

"""
import traceback
import string
import new

import pythoncom
import winerror
import build

from types import StringType, IntType, TupleType, ListType
from pywintypes import UnicodeType, IIDType

import win32com.client # Needed as code we eval() references it.
from win32com.client import NeedUnicodeConversions

debugging=0			# General debugging
debugging_attr=0	# Debugging dynamic attribute lookups.

LCID = 0x0

# These errors generally mean the property or method exists,
# but can't be used in this context - eg, property instead of a method, etc.
# Used to determine if we have a real error or not.
ERRORS_BAD_CONTEXT = [
	winerror.DISP_E_MEMBERNOTFOUND,
	winerror.DISP_E_BADPARAMCOUNT,
	winerror.DISP_E_PARAMNOTOPTIONAL,
	winerror.DISP_E_TYPEMISMATCH,
    winerror.E_INVALIDARG,
]

def debug_print(*args):
	if debugging:
		for arg in args:
			print arg,
		print

def debug_attr_print(*args):
	if debugging_attr:
		for arg in args:
			print arg,
		print

# get the dispatch type in use.
dispatchType = pythoncom.TypeIIDs[pythoncom.IID_IDispatch]
iunkType = pythoncom.TypeIIDs[pythoncom.IID_IUnknown]
_StringOrUnicodeType=[StringType, UnicodeType]
_GoodDispatchType=[StringType,IIDType,UnicodeType]
_defaultDispatchItem=build.DispatchItem

def _GetGoodDispatch(IDispatch, clsctx = pythoncom.CLSCTX_SERVER):
	if type(IDispatch) in _GoodDispatchType:
		try:
			IDispatch = pythoncom.connect(IDispatch)
		except pythoncom.ole_error:
			IDispatch = pythoncom.CoCreateInstance(IDispatch, None, clsctx, pythoncom.IID_IDispatch)
	return IDispatch

def _GetGoodDispatchAndUserName(IDispatch,userName,clsctx):
	if userName is None:
		if type(IDispatch) in _StringOrUnicodeType:
			userName = IDispatch
		else:
			userName = "<unknown>"
	return (_GetGoodDispatch(IDispatch, clsctx), userName)

def Dispatch(IDispatch, userName = None, createClass = None, typeinfo = None, UnicodeToString=NeedUnicodeConversions, clsctx = pythoncom.CLSCTX_SERVER):
	IDispatch, userName = _GetGoodDispatchAndUserName(IDispatch,userName,clsctx)
	if createClass is None:
		createClass = CDispatch
	lazydata = None
	try:
		if typeinfo is None:
			typeinfo = IDispatch.GetTypeInfo()
		try:
			#try for a typecomp
			typecomp = typeinfo.GetTypeComp()
			lazydata = typeinfo, typecomp
		except pythoncom.com_error:
			pass
	except pythoncom.com_error:
		typeinfo = None
	olerepr = MakeOleRepr(IDispatch, typeinfo, lazydata)
	return createClass(IDispatch, olerepr, userName,UnicodeToString, lazydata)

def MakeOleRepr(IDispatch, typeinfo, typecomp):
	olerepr = None
	if typeinfo is not None:
		try:
			attr = typeinfo.GetTypeAttr()
			# If the type info is a special DUAL interface, magically turn it into
			# a DISPATCH typeinfo.
			if attr[5] == pythoncom.TKIND_INTERFACE and attr[11] & pythoncom.TYPEFLAG_FDUAL:
				# Get corresponding Disp interface;
				# -1 is a special value which does this for us.
				href = typeinfo.GetRefTypeOfImplType(-1);
				typeinfo = typeinfo.GetRefTypeInfo(href)
				attr = typeinfo.GetTypeAttr()
			if typecomp is None:
				olerepr = build.DispatchItem(typeinfo, attr, None, 0)
			else:
				olerepr = build.LazyDispatchItem(attr, None)
		except pythoncom.ole_error:
			pass
	if olerepr is None: olerepr = build.DispatchItem()
	return olerepr

def DumbDispatch(IDispatch, userName = None, createClass = None,UnicodeToString=NeedUnicodeConversions, clsctx=pythoncom.CLSCTX_SERVER):
	"Dispatch with no type info"
	IDispatch, userName = _GetGoodDispatchAndUserName(IDispatch,userName,clsctx)
	if createClass is None:
		createClass = CDispatch
	return createClass(IDispatch, build.DispatchItem(), userName,UnicodeToString)

class CDispatch:
	def __init__(self, IDispatch, olerepr, userName =  None, UnicodeToString=NeedUnicodeConversions, lazydata = None):
		if userName is None: userName = "<unknown>"
		self.__dict__['_oleobj_'] = IDispatch
		self.__dict__['_username_'] = userName
		self.__dict__['_olerepr_'] = olerepr
		self.__dict__['_mapCachedItems_'] = {}
		self.__dict__['_builtMethods_'] = {}
		self.__dict__['_enum_'] = None
		self.__dict__['_unicode_to_string_'] = UnicodeToString
		self.__dict__['_lazydata_'] = lazydata

	def __call__(self, *args):
		"Provide 'default dispatch' COM functionality - allow instance to be called"
		if self._olerepr_.defaultDispatchName:
			invkind, dispid = self._find_dispatch_type_(self._olerepr_.defaultDispatchName)
		else:
			invkind, dispid = pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET, pythoncom.DISPID_VALUE
		if invkind is not None:
			allArgs = (dispid,LCID,invkind,1) + args
			return self._get_good_object_(apply(self._oleobj_.Invoke,allArgs),self._olerepr_.defaultDispatchName,None)
		raise TypeError, "This dispatch object does not define a default method"

	def __nonzero__(self):
		return 1 # ie "if object:" should always be "true" - without this, __len__ is tried.
		# _Possibly_ want to defer to __len__ if available, but Im not sure this is
		# desirable???

	def __repr__(self):
		return "<COMObject %s>" % (self._username_)

	def __str__(self):
		# __str__ is used when the user does "print object", so we gracefully
		# fall back to the __repr__ if the object has no default method.
		try:
			return str(self.__call__())
		except pythoncom.com_error, details:
			if details[0] not in ERRORS_BAD_CONTEXT:
				raise
			return self.__repr__()

	# Delegate comparison to the oleobjs, as they know how to do identity.
	def __cmp__(self, other):
		other = getattr(other, "_oleobj_", other)
		return cmp(self._oleobj_, other)

	def __int__(self):
		return int(self.__call__())

	def __len__(self):
		invkind, dispid = self._find_dispatch_type_("Count")
		if invkind:
			return self._oleobj_.Invoke(dispid, LCID, invkind, 1)
		raise TypeError, "This dispatch object does not define a Count method"

	def _NewEnum(self):
		invkind, dispid = self._find_dispatch_type_("_NewEnum")
		if invkind is None:
			return None
		
		enum = self._oleobj_.InvokeTypes(pythoncom.DISPID_NEWENUM,LCID,invkind,(13, 10),())
		import util
		return util.WrapEnum(enum, None)

	def __getitem__(self, index): # syver modified
		# Improved __getitem__ courtesy Syver Enstad
		# Must check _NewEnum before Item, to ensure b/w compat.
		if isinstance(index, IntType):
			if self.__dict__['_enum_'] is None:
				self.__dict__['_enum_'] = self._NewEnum()
			if self.__dict__['_enum_'] is not None:
				return self._get_good_object_(self._enum_.__getitem__(index))
		# See if we have an "Item" method/property we can use (goes hand in hand with Count() above!)
		invkind, dispid = self._find_dispatch_type_("Item")
		if invkind is not None:
			return self._get_good_object_(self._oleobj_.Invoke(dispid, LCID, invkind, 1, index))
		raise TypeError, "This object does not support enumeration"

	def __setitem__(self, index, *args):
		# XXX - todo - We should support calling Item() here too!
#		print "__setitem__ with", index, args
		if self._olerepr_.defaultDispatchName:
			invkind, dispid = self._find_dispatch_type_(self._olerepr_.defaultDispatchName)
		else:
			invkind, dispid = pythoncom.DISPATCH_PROPERTYPUT | pythoncom.DISPATCH_PROPERTYPUTREF, pythoncom.DISPID_VALUE
		if invkind is not None:
			allArgs = (dispid,LCID,invkind,0,index) + args
			return self._get_good_object_(apply(self._oleobj_.Invoke,allArgs),self._olerepr_.defaultDispatchName,None)
		raise TypeError, "This dispatch object does not define a default method"

	def _find_dispatch_type_(self, methodName):
		if self._olerepr_.mapFuncs.has_key(methodName):
			item = self._olerepr_.mapFuncs[methodName]
			return item.desc[4], item.dispid

		if self._olerepr_.propMapGet.has_key(methodName):
			item = self._olerepr_.propMapGet[methodName]
			return item.desc[4], item.dispid

		try:
			dispid = self._oleobj_.GetIDsOfNames(0,methodName)
		except:	### what error?
			return None, None
		return pythoncom.DISPATCH_METHOD | pythoncom.DISPATCH_PROPERTYGET, dispid

	def _ApplyTypes_(self, dispid, wFlags, retType, argTypes, user, resultCLSID, *args):
		result = apply(self._oleobj_.InvokeTypes, (dispid, LCID, wFlags, retType, argTypes) + args)
		return self._get_good_object_(result, user, resultCLSID)

	def _wrap_dispatch_(self, ob, userName = None, returnCLSID = None, UnicodeToString = NeedUnicodeConversions):
		# Given a dispatch object, wrap it in a class
		return Dispatch(ob, userName, UnicodeToString=UnicodeToString)

	def _get_good_single_object_(self,ob,userName = None, ReturnCLSID=None):
		if iunkType==type(ob):
			try:
				ob = ob.QueryInterface(pythoncom.IID_IDispatch)
				# If this works, we then enter the "is dispatch" test below.
			except pythoncom.com_error:
				# It is an IUnknown, but not an IDispatch, so just let it through.
				pass
		if dispatchType==type(ob):
			# make a new instance of (probably this) class.
			return self._wrap_dispatch_(ob, userName, ReturnCLSID)
		elif self._unicode_to_string_ and UnicodeType==type(ob):  
			return str(ob)
		else:
			return ob
		
	def _get_good_object_(self,ob,userName = None, ReturnCLSID=None):
		"""Given an object (usually the retval from a method), make it a good object to return.
		   Basically checks if it is a COM object, and wraps it up.
		   Also handles the fact that a retval may be a tuple of retvals"""
		if ob is None: # Quick exit!
			return None
		elif type(ob)==TupleType:
			return tuple(map(lambda o, s=self, oun=userName, rc=ReturnCLSID: s._get_good_single_object_(o, oun, rc),  ob))
		else:
			return self._get_good_single_object_(ob)
		
	def _make_method_(self, name):
		"Make a method object - Assumes in olerepr funcmap"
		methodName = build.MakePublicAttributeName(name) # translate keywords etc.
		methodCodeList = self._olerepr_.MakeFuncMethod(self._olerepr_.mapFuncs[name], methodName,0)
		methodCode = string.join(methodCodeList,"\n")
		try:
#			print "Method code for %s is:\n" % self._username_, methodCode
#			self._print_details_()
			codeObject = compile(methodCode, "<COMObject %s>" % self._username_,"exec")
			# Exec the code object
			tempNameSpace = {}
			exec codeObject in globals(), tempNameSpace # self.__dict__, self.__dict__
			name = methodName
			# Save the function in map.
			fn = self._builtMethods_[name] = tempNameSpace[name]
			newMeth = new.instancemethod(fn, self, self.__class__)
			return newMeth
		except:
			debug_print("Error building OLE definition for code ", methodCode)
			traceback.print_exc()
		return None
		
	def _Release_(self):
		"""Cleanup object - like a close - to force cleanup when you dont 
		   want to rely on Python's reference counting."""
		for childCont in self._mapCachedItems_.values():
			childCont._Release_()
		self._mapCachedItems_ = {}
		if self._oleobj_:
			self._oleobj_.Release()
			self.__dict__['_oleobj_'] = None
		if self._olerepr_:
			self.__dict__['_olerepr_'] = None
		self._enum_ = None

	def _proc_(self, name, *args):
		"""Call the named method as a procedure, rather than function.
		   Mainly used by Word.Basic, which whinges about such things."""
		try:
			item = self._olerepr_.mapFuncs[name]
			dispId = item.dispid
			return self._get_good_object_(apply( self._oleobj_.Invoke, (dispId, LCID, item.desc[4], 0 ) + (args) ))
		except KeyError:
			raise AttributeError, name
		
	def _print_details_(self):
		"Debug routine - dumps what it knows about an object."
		print "AxDispatch container",self._username_
		try:
			print "Methods:"
			for method in self._olerepr_.mapFuncs.keys():
				print "\t", method
			print "Props:"
			for prop, entry in self._olerepr_.propMap.items():
				print "\t%s = 0x%x - %s" % (prop, entry.dispid, `entry`)
			print "Get Props:"
			for prop, entry in self._olerepr_.propMapGet.items():
				print "\t%s = 0x%x - %s" % (prop, entry.dispid, `entry`)
			print "Put Props:"
			for prop, entry in self._olerepr_.propMapPut.items():
				print "\t%s = 0x%x - %s" % (prop, entry.dispid, `entry`)
		except:
			traceback.print_exc()

	def __LazyMap__(self, attr):
		try:
			if self._LazyAddAttr_(attr):
				debug_attr_print("%s.__LazyMap__(%s) added something" % (self._username_,attr))
				return 1
		except AttributeError:
			return 0

	# Using the typecomp, lazily create a new attribute definition.
	def _LazyAddAttr_(self,attr):
		if self._lazydata_ is None: return 0
		res = 0
		i = 0
		typeinfo, typecomp = self._lazydata_
		olerepr = self._olerepr_
		try:
			x,t = typecomp.Bind(attr,i)
			if x==1:	#it's a FUNCDESC
				r = olerepr._AddFunc_(typeinfo,t,0)
			elif x==2:	#it's a VARDESC
				r = olerepr._AddVar_(typeinfo,t,0)
			else:		#not found or TYPEDESC/IMPLICITAPP
				r=None

			if not r is None:
				key, map = r[0],r[1]
				item = map[key]
				if map==olerepr.propMapPut:
					olerepr._propMapPutCheck_(key,item)
				elif map==olerepr.propMapGet:
					olerepr._propMapGetCheck_(key,item)
				res = 1
		except:
			pass
		return res

	def __AttrToID__(self,attr):
			debug_attr_print("Calling GetIDsOfNames for property %s in Dispatch container %s" % (attr, self._username_))
			return self._oleobj_.GetIDsOfNames(0,attr)

	def __getattr__(self, attr):
		if attr[0]=='_' and attr[-1]=='_': # Fast-track.
			raise AttributeError, attr
		# If a known method, create new instance and return.
		try:
			return new.instancemethod(self._builtMethods_[attr], self, self.__class__)
		except KeyError:
			pass
		# XXX - Note that we current are case sensitive in the method.
		#debug_attr_print("GetAttr called for %s on DispatchContainer %s" % (attr,self._username_))
		# First check if it is in the method map.  Note that an actual method
		# must not yet exist, (otherwise we would not be here).  This
		# means we create the actual method object - which also means
		# this code will never be asked for that method name again.
		if self._olerepr_.mapFuncs.has_key(attr):
			return self._make_method_(attr)

		# Delegate to property maps/cached items
		retEntry = None
		if self._olerepr_ and self._oleobj_:
			# first check general property map, then specific "put" map.
			if self._olerepr_.propMap.has_key(attr):
				retEntry = self._olerepr_.propMap[attr]
			if retEntry is None and self._olerepr_.propMapGet.has_key(attr):
				retEntry = self._olerepr_.propMapGet[attr]
			# Not found so far - See what COM says.
			if retEntry is None:
				try:
					if self.__LazyMap__(attr):
						if self._olerepr_.mapFuncs.has_key(attr): return self._make_method_(attr)
						if self._olerepr_.propMap.has_key(attr):
							retEntry = self._olerepr_.propMap[attr]
						if retEntry is None and self._olerepr_.propMapGet.has_key(attr):
							retEntry = self._olerepr_.propMapGet[attr]
					if retEntry is None:
						retEntry = build.MapEntry(self.__AttrToID__(attr), (attr,))
				except pythoncom.ole_error:
					pass # No prop by that name - retEntry remains None.

		if not retEntry is None: # see if in my cache
			try:
				ret = self._mapCachedItems_[retEntry.dispid]
				debug_attr_print ("Cached items has attribute!", ret)
				return ret
			except (KeyError, AttributeError):
				debug_attr_print("Attribute %s not in cache" % attr)

		# If we are still here, and have a retEntry, get the OLE item
		if not retEntry is None:
			debug_attr_print("Getting property Id 0x%x from OLE object" % retEntry.dispid)
			try:
				ret = self._oleobj_.Invoke(retEntry.dispid,0,pythoncom.DISPATCH_PROPERTYGET,1)
			except pythoncom.com_error, details:
				if details[0] in ERRORS_BAD_CONTEXT:
					# May be a method.
					self._olerepr_.mapFuncs[attr] = retEntry
					return self._make_method_(attr)
				raise pythoncom.com_error, details
			self._olerepr_.propMap[attr] = retEntry
			debug_attr_print("OLE returned ", ret)
			return self._get_good_object_(ret)

		# no where else to look.
		raise AttributeError, "%s.%s" % (self._username_, attr)

	def __setattr__(self, attr, value):
		if self.__dict__.has_key(attr): # Fast-track - if already in our dict, just make the assignment.
			# XXX - should maybe check method map - if someone assigns to a method,
			# it could mean something special (not sure what, tho!)
			self.__dict__[attr] = value
			return
		# Allow property assignment.
		debug_attr_print("SetAttr called for %s.%s=%s on DispatchContainer" % (self._username_, attr, `value`))
		if self._olerepr_:
			# Check the "general" property map.
			if self._olerepr_.propMap.has_key(attr):
				self._oleobj_.Invoke(self._olerepr_.propMap[attr].dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, value)
				return
			# Check the specific "put" map.
			if self._olerepr_.propMapPut.has_key(attr):
				self._oleobj_.Invoke(self._olerepr_.propMapPut[attr].dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, value)
				return

		# Try the OLE Object
		if self._oleobj_:
			if self.__LazyMap__(attr):
				# Check the "general" property map.
				if self._olerepr_.propMap.has_key(attr):
					self._oleobj_.Invoke(self._olerepr_.propMap[attr].dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, value)
					return
				# Check the specific "put" map.
				if self._olerepr_.propMapPut.has_key(attr):
					self._oleobj_.Invoke(self._olerepr_.propMapPut[attr].dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, value)
					return
			try:
				entry = build.MapEntry(self.__AttrToID__(attr),(attr,))
			except pythoncom.com_error:
				# No attribute of that name
				entry = None
			if entry is not None:
				try:
					self._oleobj_.Invoke(entry.dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, value)
					self._olerepr_.propMap[attr] = entry
					debug_attr_print("__setattr__ property %s (id=0x%x) in Dispatch container %s" % (attr, entry.dispid, self._username_))
					return
				except pythoncom.com_error:
					pass
		raise AttributeError, "Property '%s.%s' can not be set." % (self._username_, attr)
