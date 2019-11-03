#[macro_use]
extern crate cpython;

use cpython::{Python, PyResult};
py_module_initializer!(rustlib, initlibrustlib, PyInit_rustlib, |py, m| {
    // m.add(py, "__doc__", "This module is implemented in Rust.")?;
    m.add(py, "load_track", py_fn!(py, load_track(path: String, size: usize, start:String, stop: String)))?;
    Ok(())
});

// TODO: if track ends -> fill vector with zeros 
fn load_track(_py: Python, path: String, size: usize, start: Strin  g, stop: String) -> PyResult<Vec<Vec<f32>>> {
    // spawn ffmpeg command line tool 
    // TODO use ffmpeg api instead of command line tool
    use std::process::Command;
    use std::io::Read;
    let process =  Command::new("ffmpeg")
    .arg("-i").arg(path)
    .arg("-ss").arg(start)  // TODO check for correct argument
    .arg("-to").arg(stop)
    .arg("-ac").arg("2")
    .arg("-ar").arg("44100")
    .arg("-bitexact")
    .arg("-acodec").arg("pcm_s16le")
    .arg("-f").arg("wav")
    .arg("pipe:1")
    .stdout(std::process::Stdio::piped())
    .spawn().unwrap();        

    let out: std::process::ChildStdout = process.stdout.unwrap();
    
    // read result with buffer into vectors
    let mut left: Vec<i16> = vec![0; size];
    let mut right: Vec<i16> = vec![0; size];
    let mut buf: [u8; 2] = [0, 0];
    let mut br = std::io::BufReader::with_capacity(400000, out);  // TODO different capacity?
    
    for i in 0..size {
        match br.read_exact(&mut buf) {
            Ok(()) => (),
            Err(_) => break,
        };
        left[i] = i16::from_le_bytes(buf);
        match br.read_exact(&mut buf) {
            Ok(()) => (),
            Err(_) => break,
        };
        right[i] = i16::from_le_bytes(buf);
    }

    //calculate max value
    //TODO better w ay?
    let mut max: i16 = 0;
    for i in 0..left.len(){
        if left[i].abs() > max{
            max = left[i].abs();
        }
    }
    for i in 0..right.len(){
        if right[i].abs() > max{
            max = right[i].abs();
        }
    }

    // cast and normalize to f32 floats between -1.0 and 1.0 
    // TODO good heuristic? what if one value is much bigger than mean values?
    let mut result_l: Vec<f32> = Vec::new();
    let mut result_r: Vec<f32> = Vec::new();

    for i in 0..left.len(){
        result_l.push((left[i] as f32) / (max as f32));
    }
    left.clear();
    left.shrink_to_fit();

    for i in 0..right.len(){
        result_r.push((right[i] as f32) / (max as f32));
    }
    right.clear();
    right.shrink_to_fit();

    // return Result as 2D vector
    let mut result: Vec<Vec<f32>> = Vec::new();
    result.push(result_l);
    result.push(result_r);
    Ok(result)
}
