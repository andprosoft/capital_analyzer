Capital Analyzer
###################

Copyright © 2022 Andriy Prots

Features
========

The Capital Analzyer can analyze your share portfolio. It will calculate
the value of your portfolio at each day. Based on this, it can provide
some interesting insight like your total gain, your share distribution,
or your personal performance compared to reference indcies.

Documentation
=============

You can find a documentation with tutorials here: 
`Documentation at Read the Docs <https://capital-analyzer.readthedocs.io/en/latest/>`_


Installation
============

Installation into Environment
+++++++++++++++++++++++++++++

To install the Capital Analyzer, first download the entire source.
In the example, the directory will be saved in ``D:\capital_analyzer``.
You must adjust the commands to your respective download location.

Open an Anaconda Prompt (Start --> Anaconda 3 --> Anaconda Prompt) and
load the desired environment:

.. code-block:: console

    conda activate env_name
    
Replace ``env_name`` with the name of the desired environment. Before 
running the installation command, change to the ``capital_analyzer`` directory:

.. code-block:: console

    D:
    cd capital_analyzer

Now, enter the following command:

.. code-block:: console

    python setup.py install
    
This will install the capital analyzer. It can now be imported in the following
way:

.. code-block:: python

    from capital_analyzer.analyze_trades import run_analyze
    
    # ...
    
  
Usage without Installation
++++++++++++++++++++++++++

You can also use the Capital Analyzer without installtion. For this,
add the following lines to your Python script (before importing modules
from the Capital Analyzer).

.. code-block:: python

    import site
    site.addsitedir('D:\capital_analyzer\python')
    
    from capital_analyzer.analyze_trades import run_analyze
    
    # ...
    
Adjust the path to the ``python`` directory in the ``site.addssitedir()``
command.
