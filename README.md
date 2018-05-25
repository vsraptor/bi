### What is Bi ?

When you use programming languages you depend on the symbols of the language to have a specific meaning, very rarely it is the case for a programming language to allow fuzzy and context based meaning, because it complicates the implementation. In natural languages concepts/symbols are both discrete and fuzzy at the same time.

To make programming languages more natural we have to embrace this dichotomy... one way to make the symbols behave this way is to represent symbols and/or context as vectors to achieve fuzziness, but still preserve discreteness.

Something like having the whole cake, but eating it too.

    That is why Bi is build on top of the so called VSA (Vector Symbolic Architecture).

....

For more information look in the /docs directory or [Bi](http://ifni.co/bi/TOC.html).

Requires the following modules :

 - bitarray
 - numpy
 - lark
 - lepl !

Test it :


    git clone git@github.com:vsraptor/bi.git bi
    cd bi/test
    time ./engine_bi.py 
    ./unify.py
 
 
