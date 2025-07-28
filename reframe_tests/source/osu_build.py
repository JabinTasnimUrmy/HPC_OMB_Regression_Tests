# reframe_tests/source_build/osu_build_source.py
import os
import reframe as rfm
import reframe.utility.sanity as sn

@rfm.simple_test
class OsuBuildSource(rfm.CompileOnlyRegressionTest):
    '''Fixture for building the OSU benchmarks from source.'''

    # --- Class Attributes (Static Properties) ---
    name = 'OsuBuildSource_v7_2'
    descr = 'Builds OSU Micro-Benchmarks v7.2 from source with foss/2023b'
    valid_systems = ['*']
    valid_prog_environs = ['foss-2023b']
    executable = ''
    num_tasks = 1
    num_tasks_per_node = 1
    tags = {'compile', 'omb', 'source', 'fixture'}
    maintainers = ['jurmy']

    omb_version = variable(str, value='7.2')

    # --- Build Preparation Hook: @run_before('compile') ---
    @run_before('compile')
    def prepare_build_environment(self):
        source_tarball = f'osu-micro-benchmarks-{self.omb_version}.tar.gz'
        source_url = f'https://mvapich.cse.ohio-state.edu/download/mvapich/{source_tarball}'
        extracted_dir = f'osu-micro-benchmarks-{self.omb_version}'
        install_prefix = os.path.join(self.stagedir, "install")

        # No pre-existing sources to copy.
        self.sourcesdir = None

        # Manage the build manually and disable the default build step.
        self.build_system = 'Make'
        self.build_system.executable = 'true'

        # Chain all build commands into a single string to ensure 'cd' works correctly.
        self.prebuild_cmds = [
            f'wget -nc {source_url} && '
            f'tar -xzf {source_tarball} && '
            f'cd {extracted_dir} && '
            f'./configure --prefix={install_prefix} CC=mpicc CXX=mpicxx && '
            f'make -j 8 && '
            f'make install'
        ]
        
        self.postbuild_cmds = []


    # --- Sanity Check Hook: @sanity_function ---
    @sanity_function
    def validate_compiled_binaries(self):
        # FINAL FIX: The installation path from the Makefile does not include the 'standard' subdirectory.
        benchmark_bin_path = os.path.join(self.stagedir, 'install', 'libexec', 
                                          'osu-micro-benchmarks', 'mpi', 
                                          'pt2pt')

        return sn.all([
            sn.assert_true(os.path.exists(os.path.join(benchmark_bin_path, 'osu_latency'))),
            sn.assert_true(os.path.exists(os.path.join(benchmark_bin_path, 'osu_bw')))
        ])
