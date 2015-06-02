from nipype.interfaces.afni import preprocess
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util

def create_anat_preproc(already_skullstripped=False):
    """ 
    Generate a workflow to do basic anatomical preprocessing (deoblique, reorient, skull-strip).

    Parameters
    ----------
    already_skullstripped : bool, optional
        True/False depending on if the anatomical files used as input have already been skull stripped.

    Returns 
    -------
    anat_preproc : workflow
     
    Notes
    -----
    Source code for the latest version can be found `on github <https://github.com/FCP-INDI/C-PAC/blob/master/CPAC/anat_preproc/anat_preproc.py>`_
    
    Workflow Inputs::
    
        inputspec.anat : nifti file or list of nifti files
            User specified anatomical (T1) image, in any of the 8 orientations
    
    Workflow Outputs::
    
        outputspec.deoblique : nifti file
            Deobliqued anatomical image. 
        outputspec.reorient : nifti file
            RPI oriented anatomical image. 
        outputspec.brain : nifti file
            Skull-stripped anatomical image.
    
    Order of preprocessing steps and command-line equivalents:

    - Deoblique. For details see `3drefit <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3drefit.html>`_::
    
        3drefit -deoblique mprage.nii.gz
        
    - Re-orient to RPI. For details see `3dresample <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dresample.html>`_::
    
        3dresample -orient RPI -prefix mprage_RPI.nii.gz -inset mprage.nii.gz 
    
    - Skull-strip. For details see `3dSkullStrip <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSkullStrip.html>`_::
    
        3dSkullStrip -input mprage_RPI.nii.gz -orig_vol mprage_RPI_3dT.nii.gz
    
    High Level Workflow Graph:
    
    .. image:: ../images/anatpreproc_graph.dot.png
       :width: 500
    
    
    Detailed Workflow Graph:
    
    .. image:: ../images/anatpreproc_graph_detailed.dot.png
       :width: 500

    Examples
    --------
    
    >>> import anat
    >>> preproc = create_anat_preproc()
    >>> preproc.inputs.inputspec.anat='sub1/anat/mprage.nii.gz'
    >>> preproc.run() #doctest: +SKIP
            
    """

    preproc = pe.Workflow(name='anat_preproc')

    """
    Configure Workflow Nodes
    """

    # The input to this workflow is usually the anatomical image specified in the CPAC subject list.
    inputNode = pe.Node(util.IdentityInterface(fields=['anat']), name='inputspec')
    # This workflow outputs deobliqued, reoriented, and skull-stripped versions of the input image.
    outputNode = pe.Node(util.IdentityInterface(fields=['deoblique', 'reorient', 'skullstrip', 'brain']), name='outputspec')

    # Set up deoblique function.
    anat_deoblique = pe.Node(interface=preprocess.Refit(), name='anat_deoblique')
    anat_deoblique.inputs.deoblique = True

    # Set up reorient function.
    anat_reorient = pe.Node(interface=preprocess.Resample(), name='anat_reorient')
    anat_reorient.inputs.orientation = 'RPI'
    anat_reorient.inputs.outputtype = 'NIFTI_GZ'

    if not already_skullstripped:
        # Set up Skull Stripping
        anat_skullstrip = pe.Node(interface=preprocess.SkullStrip(), name='anat_skullstrip')
        # Keep intensity values the same in the output as in the input.
        anat_skullstrip.inputs.options = '-orig_vol'
        anat_skullstrip.inputs.outputtype = 'NIFTI_GZ'
        
    """
    Connect Workflow Nodes
    """

    # Deoblique takes the 'raw' anatomical image as input.
    preproc.connect(inputNode, 'anat', anat_deoblique, 'in_file')
    # The deobliqued image is used as the input for Reorient.
    preproc.connect(anat_deoblique, 'out_file', anat_reorient, 'in_file')
    
    if not already_skullstripped:
        # The reoriented image is used as the input for Skullstrip.
        preproc.connect(anat_reorient, 'out_file', anat_skullstrip, 'in_file')
    
    # Output deobliqued and reoriented images.
    preproc.connect(anat_deoblique, 'out_file', outputNode, 'deoblique')
    preproc.connect(anat_reorient, 'out_file', outputNode, 'reorient')
    
    # Output skull-stripped image.
    if not already_skullstripped:
        preproc.connect(anat_skullstrip, 'out_file', outputNode, 'brain')
    else:
        preproc.connect(anat_reorient, 'out_file', outputNode, 'brain')

    return preproc
