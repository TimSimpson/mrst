Ms. Rst
=======

Ms. Rst makes it possible to avoid duplicating the docs you already have in C++ source files (such as header files making up your project's interface or .cpp files used for example code) or in Markdown files (which are preferable to .rst when repositories are being viewed in GitHub).

It does this by processing special ``.mrst`` files containing Ms. Rst directives and generating a new directory full of plain ReStructured Text files to be used by Sphinx.


How it run it
-------------

First off, this requires ``pandoc`` (the CLI program, not any Python libs you may find on PyPi). You'll need to install that and make it available on your path somehow (or just avoid Markdown files).

Take a typical Sphinx project, which will consist of a ``source`` directory and a Make file.

Throw that make file in the trash, and add a ``Pipfile`` with the following:

.. code-block:: ini

    [[source]]
    url = 'https://pypi.python.org/simple'
    verify_ssl = true
    name = 'pypi'

    [requires]
    python_version = ">= 3.6.0"

    [packages]
    msrst = "*"
    Sphinx = "*"
    typing = "*"

From now one instead of using the make file to build sphinx docs, use:

.. code-block:: bash

    pipenv install  # do this once
    pipenv run mrst build

``mrst`` will invoke Sphinx for you. To avoid this and just generate the intermediate project, run ``pipenv run mrst gen``.

By default, all docs in ``source`` gets copied into ``output/gen`` which is will then be used by Sphinx (Sphinx will put it's output in ``output/build``).

Finally, change the ``conf.py`` used by Sphinx (it's in your source directory) where it says ``source_suffix`` to include ``.mrst``.


Using Mrst Files
----------------

Files ending with ``mrst`` stand for Ms. ReStructured Text. Like Ms. Pacman, it's better than the original. There's a custom parser for them which writes them to the generated doc directory.

These files are just like ``mrst`` files but with the ``~dumpfile`` directive which takes a relative file and includes it inside of the original document.

If the given file being dumped is markdown, it's first translated using pandoc. If the file is C++, it's translated into ReStructured Text using rules described below. In either case the resulting ReStructured Text is dumped into the given file at the point where ``~dumpfile`` appears.

The ~dumpfile directive
~~~~~~~~~~~~~~~~~~~~~~~

The ~dumpfile directive looks like this:

.. code-block:: mrst

    ~dumpfile "file" <start> <end> <indent> <section>

~dumpfile takes several directives by position or via keywords. The following two examples are equivalent:

.. code-block:: mrst

    ~dumpfile "file" 0 10 4 ~

    ~dumpfile "file" end=10 start=0 section=~ indent=4

Note that the keyword argument syntax requires no spaces between the equal sign.

``start`` and ``indent`` default to 0 if not set. ``end`` defaults to the end of the file, which can also be specified explicitly using ``~``.

This next snippet means "include all text from line 12 until the end of the file and indent everything by 4 characters:

.. code-block:: mrst

    ~dumpfile "file" 12 ~ 4

This simply dumps the entire file:

.. code-block:: mrst

    ~dumpfile "file"

There's also a ``section`` keyword argument, explained below.


Markdown Conversion
-------------------

Markdown translation is provided courtesy of Pandoc. A subset of the desired Markdown file is generated in a temporary directory (so that `start` and `end` will work) and Pandoc is called to produce a file which is read and included where `~dumpfile` is seen.

One gotcha is that currently the section headers from Markdown docs are brought in as is, which may not work in the context of a larger rst project.

For example, you may want to dump the contents of the ``README.md`` file at the root of your git repo into your Sphinx generated documentation. However, if this file begins with a top header (such as ``# My Library``, which it almost certainly does) that will translate to a top level section header in your generated RsT project, which will probably mess up how your document is nested.

This can be avoided by simply skipping the first line (which contains the section header) by setting the ``start`` argument to 2 or more.


C++ to ReStructured Text Conversion
-----------------------------------

The parser reads C++ code and ignores everything until it sees special comment syntax it likes, which looks like this:

.. code-block:: c++

    // ---------------------------------------------

The important bit is that there are two slashes, a space, and then at least two hyphens.

Everything after that is included in the rst file until it sees another similar line.

Here's an example:

    // --------------------------------------------
    // Section Header
    // ===========================================
    // This describes something important.
    // -------------------------------------------/

This gets translated to the following rst:

.. code-block:: rst

    Section Header
    ==============
    This describes something important.

Note the last C++ comment is a line full of dashes ending with ``/``: that's important. It tells the translator to stop until it sees the next comment that looks like rst.

Alternatively, it's possible to make the translator scoop up actual C++ code. There's two ways to do this.

The first is to use the special directive ``// ~begin-code``. That will tell mrst to put all the code below as a C++ snippet in the rst file until it gets to ``// ~end-code``. For example:

.. code-block:: c++

    // ~begin-code

    int main() {
        // this documents how you can have a signature for main like this
        // on some platforms
    }

    // ~end-code

becomes:

.. code-block:: rst

    .. code-block:: c++

        int main() {
            // this documents how you can have a signature for main like this
            // on some platforms
        }

Instead of ``// ~end-doc`` you can also just give it a comment like described above, like this:

.. code-block:: c++

    // ------------------------------------------------------------------
    // get_customer_id
    // ------------------------------------------------------------------
    //      Grabs a customer.
    // ------------------------------------------------------------------
    template<typename Customer>
    inline int get_customer_id(Customer & c) {
        return get_id(c);
    }

    // ------------------------------------------------------------------
    // charge_customer
    // ------------------------------------------------------------------
    //      Used to charge a customer.
    // ------------------------------------------------------------------
    void charge_customer(int c_id, double money);

becomes:

.. code-block:: rst

    get_customer_id
    ---------------
    Grabs a customer.

    .. code-block:: c++

        template<typename Customer>
        inline int get_customer_id(Customer & c) {
            return get_id(c);
        }

    charge_customer
    ---------------
    Used to charge a customer.

    .. code-block:: c++

        void charge_customer(int c_id, double money);

This behavior of treating the end of the special comment block like an ``// ~end-doc`` is to make the pattern seen above easier.

If you don't want to consume the code below a special comment, end it with ``// ---/`` as seen above.


Here's an example of a class being included in rst:

.. code-block:: c++

    // --------------------------------------------
    // class RenderPlatform
    // --------------------------------------------
    //      A platform for renderers.
    //      Note how this text will get de-dented.
    // --------------------------------------------

    class RenderPlatform {
    public:
        virtual ~RenderPlatform();
        virtual const char * get_name() const;
        virtual const int priority() const;
    };
    // end-doc

the above turns into:

.. code-block:: rst

    class RenderPlatform
    --------------------
    A platform for renderers.
    Note how this text will get de-dented.

.. code-block:: c++

       class RenderPlatform {
        public:
            virtual ~RenderPlatform();
            virtual const char * get_name() const;
            virtual const int priority() const;
        };

Section headers
~~~~~~~~~~~~~~~

When parsing C++ files it's sometimes necessary to tell the C++ to rst generator what section header the incoming dumped rst should be nested under. The expected order of the section headers can be found in the `HEADERS` var defined in cpp_rst.py (note: Sphinx lets you use an arbitrary order, but you have to use the same order mrst uses in order to chnage the section headers found in C++ files).

Let's say you want to the documentation in a header file to appear under an existing section header in your rst file. You'd do this:

.. code-block:: rst

    namespace blah
    ~~~~~~~~~~~~~~

    ~dumpfile "blah/util.hpp" section=~


This would tell the C++ rst translator to start the next section after ``~``, meaning the first section header would be generated as ``^``.
