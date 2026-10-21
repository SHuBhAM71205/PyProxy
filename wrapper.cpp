#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "ProxyCore/proxy.h"

#include <algorithm>
#include <cctype>
#include <exception>
#include <new>
#include <set>
#include <string>

typedef struct
{
    PyObject_HEAD
    ProxyServer *server;
    int port;
    bool running;
    std::set<std::string> restrictedSites;
    PyObject *eventCallback;
} ProxyObject;

static PyTypeObject ProxyType = {
    PyVarObject_HEAD_INIT(nullptr, 0)
};



// Standard Cpp function not related to python i.e. Cpp helping function...
//----------

static std::string
Proxy_normalizeSite(const char *site)
{
    std::string normalized(site);
    std::transform(
        normalized.begin(), normalized.end(), normalized.begin(),
        [](unsigned char character)
        { return static_cast<char>(std::tolower(character)); });
    if (normalized.compare(0, 4, "www.") == 0)
        normalized.erase(0, 4);
    return normalized;
}

//-----------

/* 
called by python interpreter.. so it means when we call say 

v = ClassName()

it create the mem allocation and this is the function called for that task of allocation.. :
*/
static PyObject *
Proxy_new(PyTypeObject *type, PyObject *, PyObject *)
{
    ProxyObject *self = reinterpret_cast<ProxyObject *>(type->tp_alloc(type, 0));
    if (self != nullptr)
    {
        self->server = nullptr;
        self->port = 8080;
        self->running = false;
        new (&self->restrictedSites) std::set<std::string>();
        self->eventCallback = nullptr;
    }
    return reinterpret_cast<PyObject *>(self);
}

/*
    As name says exact same work is done by init just cppp ver
*/
static int
Proxy_init(ProxyObject *self, PyObject *args, PyObject *kwargs)
{
    int port = 8080;
    static char *keywords[] = {const_cast<char *>("port"), nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|i:Proxy", keywords, &port))
        return -1;
    if (port < 1 || port > 65535)
    {
        PyErr_SetString(PyExc_ValueError, "port must be between 1 and 65535");
        return -1;
    }

    if (self->server != nullptr)
    {
        if (self->running)
            self->server->stop();
        delete self->server;
        self->server = nullptr;
    }
    self->running = false;
    self->restrictedSites.clear();
    self->port = port;
    return 0;
}


/*
    when delete is called in python this function is called internally..
*/
static void
Proxy_dealloc(ProxyObject *self)
{
    if (self->server != nullptr)
    {
        if (self->running)
            self->server->stop();
        delete self->server;
    }
    Py_XDECREF(self->eventCallback);
    self->eventCallback = nullptr;
    self->restrictedSites.~set<std::string>();
    Py_TYPE(self)->tp_free(reinterpret_cast<PyObject *>(self));
}


// all the method we want i.e. obj methods means the one created by useer
// It is same as wrriting python but in cpp ::))
//--------------------------------------------------------

/*
    createServer
    callsed as
    obj.createServer()
*/
static bool
Proxy_createServer(ProxyObject *self)
{
    try
    {
        self->server = new ProxyServer(self->port);
        if (self->eventCallback != nullptr)
        {
            self->server->setnamedEventCallback(
                [self](const std::string &name, int value)
                {
                    PyGILState_STATE gilState = PyGILState_Ensure();
                    if (self->eventCallback != nullptr)
                    {
                        PyObject *result = PyObject_CallFunction(
                            self->eventCallback, "si", name.c_str(), value);
                        if (result == nullptr)
                            PyErr_WriteUnraisable(self->eventCallback);
                        else
                            Py_DECREF(result);
                    }
                    PyGILState_Release(gilState);
                });
        }
        for (const std::string &site : self->restrictedSites)
            self->server->addRestrictedSites(site);
        return true;
    }
    catch (const std::exception &error)
    {
        delete self->server;
        self->server = nullptr;
        PyErr_SetString(PyExc_RuntimeError, error.what());
        return false;
    }
}

static PyObject *
Proxy_setEventCallback(ProxyObject *self, PyObject *callback)
{
    if (callback != Py_None && !PyCallable_Check(callback))
    {
        PyErr_SetString(PyExc_TypeError, "callback must be callable or None");
        return nullptr;
    }
    if (self->running)
    {
        PyErr_SetString(PyExc_RuntimeError, "stop the proxy before changing its event callback");
        return nullptr;
    }

    Py_XINCREF(callback == Py_None ? nullptr : callback);
    Py_XDECREF(self->eventCallback);
    self->eventCallback = callback == Py_None ? nullptr : callback;

    if (self->server != nullptr)
    {
        if (self->eventCallback == nullptr)
        {
            self->server->setnamedEventCallback({});
        }
        else
        {
            self->server->setnamedEventCallback(
                [self](const std::string &name, int value)
                {
                    PyGILState_STATE gilState = PyGILState_Ensure();
                    if (self->eventCallback != nullptr)
                    {
                        PyObject *result = PyObject_CallFunction(
                            self->eventCallback, "si", name.c_str(), value);
                        if (result == nullptr)
                            PyErr_WriteUnraisable(self->eventCallback);
                        else
                            Py_DECREF(result);
                    }
                    PyGILState_Release(gilState);
                });
        }
    }
    Py_RETURN_NONE;
}

/*
    save restricted site
*/
static void
Proxy_saveRestrictedSites(ProxyObject *self)
{
    if (self->server != nullptr)
        self->restrictedSites = self->server->getRestrictedSites();
}

/*
    start the server
*/
static PyObject *
Proxy_start(ProxyObject *self, PyObject *)
{
    if (self->running)
        Py_RETURN_NONE;
    if (self->server == nullptr && !Proxy_createServer(self))
        return nullptr;

    try
    {
        self->server->start();
        self->running = true;
    }
    catch (const std::exception &error)
    {
        PyErr_SetString(PyExc_RuntimeError, error.what());
        return nullptr;
    }
    Py_RETURN_NONE;
}

/*
    stop the server
*/
static PyObject *
Proxy_stop(ProxyObject *self, PyObject *)
{
    if (self->server != nullptr)
    {
        Proxy_saveRestrictedSites(self);
        if (self->running)
            self->server->stop();
        delete self->server;
        self->server = nullptr;
        self->running = false;
    }
    Py_RETURN_NONE;
}

/*
    restart the server
*/
static PyObject *
Proxy_restart(ProxyObject *self, PyObject *)
{
    Proxy_saveRestrictedSites(self);
    if (self->server != nullptr)
    {
        if (self->running)
            self->server->stop();
        delete self->server;
        self->server = nullptr;
        self->running = false;
    }

    if (!Proxy_createServer(self))
        return nullptr;
    try
    {
        self->server->start();
        self->running = true;
    }
    catch (const std::exception &error)
    {
        delete self->server;
        self->server = nullptr;
        PyErr_SetString(PyExc_RuntimeError, error.what());
        return nullptr;
    }
    Py_RETURN_NONE;
}


/*
    blah blah blah com one same as above
*/
static PyObject *
Proxy_addRestrictedSites(ProxyObject *self, PyObject *args)
{
    const char *site = nullptr;
    if (!PyArg_ParseTuple(args, "s:add_restricted_sites", &site))
        return nullptr;

    std::string value = Proxy_normalizeSite(site);
    if (self->server != nullptr)
    {
        if (!self->server->addRestrictedSites(value))
            Py_RETURN_FALSE;
    }
    else if (!self->restrictedSites.insert(value).second)
    {
        Py_RETURN_FALSE;
    }
    Proxy_saveRestrictedSites(self);
    self->restrictedSites.insert(value);
    Py_RETURN_TRUE;
}

/*
    same as above
*/
static PyObject *
Proxy_removeRestrictedSites(ProxyObject *self, PyObject *args)
{
    const char *site = nullptr;
    if (!PyArg_ParseTuple(args, "s:remove_restricted_sites", &site))
        return nullptr;

    std::string value = Proxy_normalizeSite(site);
    bool removed = self->server != nullptr
                       ? self->server->removeRestrictedSites(value)
                       : self->restrictedSites.erase(value) != 0;
    if (removed)
    {
        Proxy_saveRestrictedSites(self);
        self->restrictedSites.erase(value);
    }
    return PyBool_FromLong(removed);
}

/*
    same
*/
static PyObject *
Proxy_getRestrictedSites(ProxyObject *self, PyObject *)
{
    Proxy_saveRestrictedSites(self);
    PyObject *sites = PyList_New(
        static_cast<Py_ssize_t>(self->restrictedSites.size()));
    if (sites == nullptr)
        return nullptr;

    Py_ssize_t index = 0;
    for (const std::string &site : self->restrictedSites)
    {
        PyObject *value = PyUnicode_FromStringAndSize(
            site.data(), static_cast<Py_ssize_t>(site.size()));
        if (value == nullptr)
        {
            Py_DECREF(sites);
            return nullptr;
        }
        PyList_SET_ITEM(sites, index++, value);
    }
    return sites;
}

// obj method ends
//---------------------------------------------------------


// weell we do need something to bind 
//------------------

static PyMethodDef Proxy_methods[] = {
    {"start", reinterpret_cast<PyCFunction>(Proxy_start), METH_NOARGS,
     "Start the proxy server."},
    {"stop", reinterpret_cast<PyCFunction>(Proxy_stop), METH_NOARGS,
     "Stop the proxy server."},
    {"restart", reinterpret_cast<PyCFunction>(Proxy_restart), METH_NOARGS,
     "Restart the proxy server."},
    {"add_restricted_sites",
     reinterpret_cast<PyCFunction>(Proxy_addRestrictedSites), METH_VARARGS,
     "Add a restricted site and return whether it was added."},
    {"remove_restricted_sites",
     reinterpret_cast<PyCFunction>(Proxy_removeRestrictedSites), METH_VARARGS,
     "Remove a restricted site and return whether it was removed."},
    {"get_restricted_sites",
     reinterpret_cast<PyCFunction>(Proxy_getRestrictedSites), METH_NOARGS,
     "Return the restricted sites."},
    {"set_event_callback",
     reinterpret_cast<PyCFunction>(Proxy_setEventCallback), METH_O,
     "Set a callback receiving (event_name, value) from proxy events."},
    {nullptr, nullptr, 0, nullptr}};

static PyModuleDef proxyModule = {
    PyModuleDef_HEAD_INIT,
    "pyproxy_native",
    "Python bindings for ProxyServer.",
    -1,
    nullptr};

PyMODINIT_FUNC
PyInit_pyproxy_native()
{
    ProxyType.tp_name = "pyproxy_native.Proxy";
    ProxyType.tp_doc = "Proxy server.";
    ProxyType.tp_basicsize = sizeof(ProxyObject);
    ProxyType.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
    ProxyType.tp_new = Proxy_new;
    ProxyType.tp_init = reinterpret_cast<initproc>(Proxy_init);
    ProxyType.tp_dealloc = reinterpret_cast<destructor>(Proxy_dealloc);
    ProxyType.tp_methods = Proxy_methods;

    if (PyType_Ready(&ProxyType) < 0)
        return nullptr;

    PyObject *module = PyModule_Create(&proxyModule);
    if (module == nullptr)
        return nullptr;

    Py_INCREF(&ProxyType);
    if (PyModule_AddObject(module, "Proxy",
                           reinterpret_cast<PyObject *>(&ProxyType)) < 0)
    {
        Py_DECREF(&ProxyType);
        Py_DECREF(module);
        return nullptr;
    }
    return module;
}
