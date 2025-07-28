
# ReFrame configuration for ULHPC cluster

site_configuration = {
  'systems': [
    {
      'name': 'iris',
      'descr': 'Iris cluster',
      'hostnames': [r'iris-[0-9]{3}'],
      'modules_system': 'lmod',
      'partitions': [
        {
          'name': 'batch',
          'descr': 'Iris Skylake compute nodes via batch partition',
          'scheduler': 'slurm',
          'launcher': 'srun',
          'access': ['--partition=batch', '--qos=normal', '-C skylake', '--time=0-00:10:00'],
          'environs': ['foss-2023b'],
          'max_jobs': 8, # 8? probably should be a diff number
          'sched_options': {
            'use_nodes_option': True
          }
        },
      ]
    },
    {
      'name': 'aion',
      'descr': 'Aion cluster',
      'hostnames': [r'aion-[0-9]{4}'],
      'modules_system': 'lmod',
      'partitions': [
        {
          'name': 'batch',
          'descr': 'Aion compute nodes',
          'scheduler': 'slurm',
          'launcher': 'srun',
          'access': ['--partition=batch', '--qos=normal', '--time=0-00:10:00'],
          'environs': ['foss-2023b'],
          'max_jobs': 8,
          'sched_options': {
            'use_nodes_option': True
          }
        }
      ]
    }
  ],

  'environments': [
    {
      'name': 'foss-2023b',
      'modules': [
        'env/testing/2023b',
        'toolchain/foss/2023b',
        'tools/EasyBuild'
      ],
      
      # compilers for this environment
      'cc': 'mpicc',
      'cxx': 'mpicxx',
      'ftn': 'mpifort',
    },
    # We can add other environments later (e.g., EESSI)
  ],
}
