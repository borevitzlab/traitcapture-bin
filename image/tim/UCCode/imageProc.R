
########################################################################################################################
# define coordinates for each flat
########################################################################################################################

###save the images for defining coordinates

library(EBImage)

all.tray <- c("cam5", "cam2") ###for example, two training flats

for (i in 1:length(all.tray)){
   which.tray <- all.tray[i]

   day.dir <- dir( paste("/home/borevitzlab/g2data/albums/Growth Chambers_001/Growth Chambers/Cams/",
      which.tray, sep=""), full.names=T)
   ###each flat has a folder, images were arranged into sub-folders, each of which represents a single day

   n <- 30 ###the day within which a new coordinate is needed, for example the first day, or the day when flat position was changed

   files <- dir(day.dir[n], full.names=T)
   int <- 0
   iter <- 0
   while(  int < 7e6 & iter <= 10){ ###pick a good image
      img <- readImage(sample(files, 1), TrueColor)
      int <- mean(img)
      iter <- iter+1
   }

   pix <- img@.Data[,,1]
   save(pix, file=paste("/home/xuzhang/image/coord/", which.tray, ".RData", sep=""), compress=T )
}


###define coordinates

get_matrix_coord <- function(coord_list, pixel_matrix) { ###function to convert from plot coordinates to matrix coordinates
   len <- length(coord_list[[1]])
   coord_list$y <- rep(1,len) - coord_list$y ###Flip y-coordinates back
   coord_list$x <- coord_list$x*dim(pixel_matrix)[1]
   coord_list$y <- coord_list$y*dim(pixel_matrix)[2]
   return(coord_list)
 }

i <- 2
load ( paste(all.tray[i], ".RData", sep="") )
image( pix[, ncol(pix):1], col=gray(1:100/100)) ###Flip to retain orientation

cat('Click: [1] plot window to select, [2] top left, [3] bottom right\n')  ### Get pot size
pot_img <- locator(2) ###Clockwise, starting from top left
pot <- get_matrix_coord(pot_img, pix)
x_pix <- round((pot$x[2]-pot$x[1])/2)
y_pix <- round((pot$y[2]-pot$y[1])/2)

n_rows <- 5 ###the number of rows
n_cols <- 6 ###the number of columns
n_missing <- 1 ###the number of missing cells

centers_img <- locator(n_rows*n_cols - n_missing) ###Clockwise, starting from top left to bottom right
centers <- get_matrix_coord(centers_img, pix)

centers <- data.frame(centers)
top_left     <- data.frame(x = centers$x - x_pix, y = centers$y - y_pix)
bottom_right <- data.frame(x = centers$x + x_pix, y = centers$y + y_pix)

top_left[ top_left <0 ] <- 0
bottom_right[ bottom_right[,1] > dim(pix)[1], 1 ] <- dim(pix)[1]
bottom_right[ bottom_right[,2] > dim(pix)[2], 2 ] <- dim(pix)[2]

save(top_left,  bottom_right,   file= paste( all.tray[i], "_coords.RData", sep="") , compress=T)


########################################################################################################################
# get picture time using ExifTool
########################################################################################################################

all.tray <- c("cam5", "cam2")

dir=`dir /home/borevitzlab/g2data/albums/Growth\ Chambers_001/Growth\ Chambers/Cams/cam22`
rm -r /home/xuzhang/image/camera.time/cam2
mkdir /home/xuzhang/image/camera.time/cam2

for i in $dir
   do{
   /sw/perl/bin/exiftool /home/borevitzlab/g2data/albums/Growth\ Chambers_001/Growth\ Chambers/Cams/cam22/${i}/* | grep 'File Name' >> /home/xuzhang/image/camera.time/cam22/${i}.filename
   /sw/perl/bin/exiftool /home/borevitzlab/g2data/albums/Growth\ Chambers_001/Growth\ Chambers/Cams/cam22/${i}/* | grep 'Create Date' >> /home/xuzhang/image/camera.time/cam22/${i}.timelap
   echo $i
  }
  done
  echo $?


##########################################################################################################################
# crop image for each flat
##########################################################################################################################

library(EBImage)

all.tray <- c("cam5", "cam2")

which.tray <- all.tray[1] ###select a flat

out.dir <- tempdir()
dir.create( paste("/home/xuzhang/image/crop/", which.tray, sep="") )
crop.dir <- paste("/home/xuzhang/image/crop/", which.tray, "/", sep="")

file <- dir(crop.dir, full.names=T)
file.remove(file)

layout <- scan( paste("/home/xuzhang/image/tray.layout/", which.tray, ".txt", sep=""), what="a", sep="\t" ) ###the layout of plants within the flat
plant <- layout[ length(layout):1 ] ###the order is reversed to cropping order, facing barcode

tray.dir <- paste("/home/borevitzlab/g2data/albums/Growth Chambers_001/Growth Chambers/Cams/", which.tray, sep="")
day.dir <- dir (tray.dir, full.names=T)

day.dir <- day.dir[ c(12:48) ] ###for example, cam5 were analyzed from 2/12 to 3/20

load ( paste("/home/xuzhang/image/coord/", which.tray, "_coords.RData", sep="") ) ###here use the same coords assuming flat not move

for (k in 1:length(day.dir) ){ ###which day
   which.day <- sub( paste(tray.dir, "/", sep=""), "", day.dir[k], fixed=T)

   filename <-  matrix( scan( paste("/home/xuzhang/image/camera.time/", which.tray, "/", which.day, ".filename", sep=""), what="a"), byrow=T, nc=4)[,4]
   time.lap <-  matrix( scan( paste("/home/xuzhang/image/camera.time/", which.tray, "/", which.day, ".timelap", sep=""), what="a"), byrow=T, nc=5)[,4:5]
   time.lap <-  paste( gsub(":", "-", time.lap[,1], fixed=T), time.lap[,2] )
   time.lap <-   as.numeric( as.POSIXct( strptime(time.lap, format="%Y-%m-%d %H:%M:%S") ) )

   time.dir <- dir(day.dir[k], full.names=T)
   time.lap <- time.lap[ which( file.info(time.dir)[, "size"]>2.5e+6) ] #remove blank picture or truncated picture
   time.dir <- time.dir[ which( file.info(time.dir)[, "size"]>2.5e+6) ]
   time.idx <- sort.int(time.lap, index.return=T)$ix
   time.dir <- time.dir[time.idx]   ###images in time order
   time.lap <- time.lap[time.idx]
   time.idx <- which( diff(time.lap) <300 ) ###images are at least 5min apart
   if(length(time.idx)>0)
   {
      time.idx <- time.idx+1
      time.dir <- time.dir[- time.idx]
      time.lap <- time.lap[- time.idx]
   }

   for (i in 1:length(time.dir) ) ###which time
   {
      img <- readImage(time.dir[i], TrueColor)
      img <- normalize2(img)

      for (n in 1:length(plant))
      {
         tmp.crop <-  img[ top_left[n,1]:bottom_right[n,1], top_left[n,2]:bottom_right[n,2], 1]  ###crop image
         writeImage(tmp.crop, file.path(crop.dir, paste(plant[n], "_day", k, "_time", i, ".jpg", sep="") )  )
      }
   } ###close of time

   cat (k, "\n")
} ###close of day


#########################################################################################################################
# quality check of the images taken at noontime across days
#########################################################################################################################

 library(EBImage)

 all.tray <- c("cam5", "cam2")

 day.cut <- matrix(scan("/home/xuzhang/image2/daycut.txt", what=1, comment.char="#", nlines=length(all.tray)), byrow=T, nc=3) ###the mean light intensity thresholds to distinguish day and night pictures
 extra.day.cut <- matrix(scan("/home/xuzhang/image2/daycut.txt", what=1, skip=length(all.tray)), byrow=T, nc=3) ###some unusuall tray, mean light intensity thresholds to disguish day and night pictures

 labels <- matrix(scan( "/home/xuzhang/image2/labels.txt", what="a", sep="\t"), byrow=T, nc=2) ###some flats have green labels and sticks

 fit.day <- function(x1, x2) { pred <- 0.12 + x1*0.475 - x2*0.00000130 }  ###function for estimation of background threshold for noontime images

 m <- 13 ###select a flat

 which.tray <- all.tray[m]

 dir.create( paste("/home/xuzhang/image2/view/", which.tray, sep="") )

 out.dir <- tempdir()
 html.dir <- paste("/home/xuzhang/image2/view/", which.tray, "/", sep="")
 crop.dir <- paste("/home/xuzhang/image2/crop/", which.tray, "/", sep="")

 layout <- scan( paste("/home/xuzhang/image2/tray.layout/", which.tray, ".txt", sep=""), what="a", sep="\t")
 plant <- layout[ length(layout):1 ] #the order is reversed, facing barcode or not

 tray.dir <- paste("/home/borevitzlab/g2data/albums/Growth Chambers_001/Growth Chambers/Cams/", which.tray, sep="")

 coords <- matrix( scan( paste("/home/xuzhang/image2/matchCoord.", which.tray, ".txt", sep=""), what="a", sep="\t") , byrow=T, nc=3)  ###the spread sheet of image records
 day.dir <- sub(tray.dir, "", coords[, 1])
 day.dir <- matrix(unlist(strsplit(day.dir, "/")), byrow=T, nc=3)[,2]
 day.dir <- names(table(day.dir))

 for (n in 1:length(plant)) ###analyze plants in order
 {
   summary.size <- summary.f <- c()

   for (k in 1:length(day.dir))    ###which day
   {
    which.day <- day.dir[k]

    filename <-  matrix( scan( paste("/home/xuzhang/image2/camera.time/", which.tray, "/", which.day, ".filename", sep=""), what="a"), byrow=T, nc=4)[,4]
    time.lap <-  matrix( scan( paste("/home/xuzhang/image2/camera.time/", which.tray, "/", which.day, ".timelap", sep=""), what="a"), byrow=T, nc=5)[,4:5]
    time.lap <-  paste( gsub(":", "-", time.lap[,1], fixed=T), time.lap[,2] )
    time.lap <-  as.numeric( as.POSIXct( strptime(time.lap, format="%Y-%m-%d %H:%M:%S") ) )
    time.dir <- paste(tray.dir, which.day, filename, sep="/")

    which.coord <- coords[ grep(which.day, coords[,1]), ]
    time.lap <- time.lap[ match (which.coord [,1], time.dir)]
    time.dir <- time.dir[ match (which.coord [,1], time.dir)]
    time.order <- c(1:length(time.dir))
    time.order <- time.order[ which( !is.na( which.coord[,3]) ) ]
    time.lap <- time.lap[ which( !is.na( which.coord[,3]) ) ]

    img <- file.path(crop.dir, paste(plant[n], "_day", k, "_time", time.order, ".jpg", sep="") )
    if (k==1)   {tmp.img <- readImage(img[1], TrueColor); img.dim <- dim(tmp.img); size <- 1000 }
    data <- array(0, c(img.dim[1:2], length(img)) )  ###read in image stacks and trim to the same size
    for (i in 1:length(img))
    {
     tmp.img <- readImage(img[i], TrueColor)
     min.r <- min( dim(tmp.img)[1], img.dim[1] )
     min.c <- min( dim(tmp.img)[2], img.dim[2] )
     tmp.data <- tmp.img@.Data[1:min.r, 1:min.c, 1]
     data[1:min.r,1:min.c,i] <- tmp.data
    }
    img <- Image( data, dim=c(img.dim[1:2], length(img)), TrueColor )

    ###remove the night images
    mean.int <- apply(channel(img, "g")-channel(img, "r"), 3, mean)
    ifelse(k < day.cut[m,3], mean.idx <- which(mean.int < day.cut[m,1]), mean.idx <- which(mean.int < day.cut[m,2]) )
    day.cut.idx <- which(extra.day.cut[,1]==m & extra.day.cut[,2]==n )
    if(length(day.cut.idx)>0) mean.idx <- which(mean.int < extra.day.cut[day.cut.idx, 3] )

    tmp.idx <- mean.idx[ which.max(mean.int[mean.idx]) ]
    tmp.img <- img[,,tmp.idx] ###the noontime image, can use other criteria
    tmp.r <- channel(tmp.img, "r"); tmp.g <- channel(tmp.img, "g"); tmp.b <- channel(tmp.img, "b")
    tmp.rb <- tmp.r*(tmp.r/(tmp.r+tmp.b) ) + tmp.b*(tmp.b/(tmp.r+tmp.b) )

    delta <- 0.35* (50000-size)/50000
    if( delta < 0 ) delta <- 0
    filter <- (tmp.g-tmp.r)*(1-delta) + (tmp.g-tmp.rb)*delta ###color filtering
    mean.f <- mean(filter, na.rm=T)
    summary.f <- c(summary.f, mean.f)
    t <- fit.day(mean.f, size) ###background threshold
    if( t < 0 ) t <- 0
    dist <-  try( distmap(filter, t=t) )
    if (length(dist)==1)
    {
     writeImage(tmp.img, file.path(out.dir, paste("img", k, ".jpg", sep="")) )
     idx <- readImage( file.path(out.dir, paste("idx", k-1, ".jpg", sep="")) )
     writeImage(Image(idx), file.path(out.dir, paste("idx", k, ".jpg", sep="")) )
     summary.size <- c(summary.size, size)
     next
    }
    widx <- watershed(dist, tolerance=1, ext=3 )
    ft <- hullFeatures ( widx )

    ### remove noise objects
    ifelse (size <= 20000, noise.cut <- 30, noise.cut <- 60)
    idx <- rmObjects(widx,  list( which( ft[,"h.s"] < noise.cut  | ft[,"h.p"] < noise.cut | ft[,"h.s"]/ft[,"h.p"] < 1.5)))

    ###remove the green labels and sticks from image
    which.label <- labels[ which( labels[,1] == paste(which.tray, plant[n], k, sep=".") ), 2]
    if ( !is.na(which.label) )
    {
     load ( paste("/home/xuzhang/image2/labels/", which.tray, "/", which.label, ".RData", sep="") )
     idx[label] <- 0
    }

    idx[tmp.img==0] <- 0

    ft <- hullFeatures(idx)
    size <- sum(ft[,"h.s"])
    summary.size <- c(summary.size, size)

    writeImage(tmp.img, file.path(out.dir, paste("img", k, ".jpg", sep="")) )
    writeImage(Image(idx), file.path(out.dir, paste("idx", k, ".jpg", sep="")) )

    cat(m, "\t", n, "\t", k, "\n")

   } ###close of day

   img <- readImage( file.path(out.dir, paste("img", 1:k, ".jpg", sep="")), TrueColor )
   idx <- readImage( file.path(out.dir, paste("idx", 1:k, ".jpg", sep="")) )
   writeImage( tile(img, nx=12), file.path(html.dir, paste(plant[n], ".midimg.jpg", sep="")))
   writeImage( tile(idx, nx=12), file.path(html.dir, paste(plant[n], ".mididx.jpg", sep="")))
   file <- dir(out.dir, full.names=T)
   file.remove(file)

 } ###close of plant



#########################################################################################################################
# quality check of images taken across time points within each day #########################################################################################################################


 library(EBImage)

 all.tray <- c("cam5", "cam2")

 day.cut <- matrix(scan("/home/xuzhang/image2/daycut.txt", what=1,comment.char="#", nlines=length(all.tray)), byrow=T, nc=3) ###the mean light intensity thresholds to distinguish day and night pictures
 extra.day.cut <- matrix(scan("/home/xuzhang/image2/daycut.txt", what=1, skip=length(all.tray)), byrow=T, nc=3)  ###some unusuall tray, mean light intensity thresholds to disguish day and night pictures
 labels <- matrix(scan( "/home/xuzhang/image2/labels.txt", what="a", sep="\t"), byrow=T, nc=2)

 fit.day <- function(x1, x2) { pred <- 0.12 + x1*0.475 - x2*0.00000130 } ###function for estimation of background threshold for noontime images

 m <- 31 ###select a flat

 fit.day1 <- function(x1, x2) {  0.335 + x1*0.470 - x2*0.00000146 }  ###general function for estimate background threshod

 which.tray <- all.tray[m]


 dir.create( paste("/home/xuzhang/image2/view1/", which.tray, sep="") )

 html.dir <- paste("/home/xuzhang/image2/view1/", which.tray, "/", sep="")
 crop.dir <- paste("/home/xuzhang/image2/crop/", which.tray, "/", sep="")

 out.dir <- tempdir()

 layout <- scan( paste("/home/xuzhang/image2/tray.layout/", which.tray, ".txt", sep=""), what="a", sep="\t")
 plant <- layout[ length(layout):1 ] ###the order is reversed, facing barcode or not

 tray.dir <- paste("/home/borevitzlab/g2data/albums/Growth Chambers_001/Growth Chambers/Cams/", which.tray, sep="")

 coords <- matrix( scan( paste("/home/xuzhang/image2/matchCoord.", which.tray, ".txt", sep=""), what="a", sep="\t") , byrow=T, nc=3) ###spreadsheet for image records
 day.dir <- sub(tray.dir, "", coords[, 1])
 day.dir <- matrix(unlist(strsplit(day.dir, "/")), byrow=T, nc=3)[,2]
 day.dir <- names(table(day.dir))

 for (n in 32:length(plant)) ###analyze plants in order
 {
  summary.f <-  summary.size  <- c()

  for (k in 1:length(day.dir) )    ###which day
  {
   which.day <- day.dir[k]

   filename <-  matrix( scan( paste("/home/xuzhang/image2/camera.time/", which.tray, "/", which.day, ".filename", sep=""), what="a"), byrow=T, nc=4)[,4]
   time.lap <-  matrix( scan( paste("/home/xuzhang/image2/camera.time/", which.tray, "/", which.day, ".timelap", sep=""), what="a"), byrow=T, nc=5)[,4:5]
   time.lap <-  paste( gsub(":", "-", time.lap[,1], fixed=T), time.lap[,2] )
   time.lap <-  as.numeric( as.POSIXct( strptime(time.lap, format="%Y-%m-%d %H:%M:%S") ) )
   time.dir <- paste(tray.dir, which.day, filename, sep="/")

   which.coord <- coords[ grep(which.day, coords[,1]), ]
   time.lap <- time.lap[ match (which.coord [,1], time.dir)]
   time.dir <- time.dir[ match (which.coord [,1], time.dir)]
   time.order <- c(1:length(time.dir))
   time.order <- time.order[ which( !is.na( which.coord[,3]) ) ]
   time.lap <- time.lap[ which( !is.na( which.coord[,3]) ) ]

   img <- file.path(crop.dir, paste(plant[n], "_day", k, "_time", time.order, ".jpg", sep="") ) ###read in image stack and trim images to the same size
   if (k==1)   {tmp.img <- readImage(img[1], TrueColor); img.dim <- dim(tmp.img); size <- 1000}
   data <- array(0, c(img.dim[1:2], length(img)) )
   for (i in 1:length(img))
   {
    tmp.img <- readImage(img[i], TrueColor)
    min.r <- min( dim(tmp.img)[1], img.dim[1] )
    min.c <- min( dim(tmp.img)[2], img.dim[2] )
    tmp.data <- tmp.img@.Data[1:min.r, 1:min.c, 1]
    data[1:min.r,1:min.c,i] <- tmp.data
   }
   img <- Image( data, dim=c(img.dim[1:2], length(img)), TrueColor )

   ###remove nighttime images
   mean.int <- apply(channel(img, "g")-channel(img, "r"), 3, mean)
   ifelse(k < day.cut[m,3], mean.idx <- which(mean.int < day.cut[m,1]), mean.idx <- which(mean.int < day.cut[m,2]) )
   day.cut.idx <- which(extra.day.cut[,1]==m & extra.day.cut[,2]==n )
   if(length(day.cut.idx)>0) mean.idx <- which(mean.int < extra.day.cut[day.cut.idx, 3] )

   tmp.idx <- mean.idx[ which.max(mean.int[mean.idx]) ]
   tmp.img <- img[,,tmp.idx]
   tmp.r <- channel(tmp.img, "r"); tmp.g <- channel(tmp.img, "g"); tmp.b <- channel(tmp.img, "b")
   tmp.rb <- tmp.r*(tmp.r/(tmp.r+tmp.b) ) + tmp.b*(tmp.b/(tmp.r+tmp.b) )

   delta <- 0.35* (50000-size)/50000
   if( delta < 0 ) delta <- 0
   filter <- (tmp.g-tmp.r)*(1-delta) + (tmp.g-tmp.rb)*delta ###color filtering
   mean.f <- mean(filter, na.rm=T)
   t <- fit.day(mean.f, size)
   if( t < 0 ) t <- 0
   dist <- try( distmap(filter, t=t) )
   if( length(dist)==1)
   {
    writeImage(tile( Image(array( rep(tmp.img,3), dim=c(img.dim[1:2],3))), nx=3), file.path(out.dir, paste("img", k, ".jpg", sep="")) )
    writeImage(tile( Image(array( rep(tmp.img,3), dim=c(img.dim[1:2],3))), nx=3), file.path(out.dir, paste("idx", k, ".jpg", sep="")) )
    summary.f <- c(summary.f, rep(mean.f, 3))
    summary.size <- c(summary.size, rep(size, 3))
    next
   }

   widx <-  watershed(dist, tolerance=1, ext=3 )
   ft <- hullFeatures ( widx )
   idx <- rmObjects(widx,  list( which( ft[,"h.effr"]<=5 | ft[,"h.sf"]>5 ) ) )

   ###remove green labels and sticks
   which.label <- labels[ which( labels[,1] == paste(which.tray, plant[n], k, sep=".") ), 2]
   if ( !is.na(which.label) )
   {
    load ( paste("/home/xuzhang/image2/labels/", which.tray, "/", which.label, ".RData", sep="") )
    idx[label] <- 0
   }

   idx[ tmp.img==0] <- 0

   ft <- hullFeatures(idx)
   size <-  sum(ft[,"h.s"]) ###the rosette size at noontime

   delta <- 0.35* (50000-size)/50000
   if( delta < 0 ) delta <- 0

   mean.idx <- c(mean.idx[c(1,2)], tmp.idx) ###the images taken at dawn and noontime, as representatives
   img <- img[,,mean.idx]
   r <- channel(img, "r"); g <- channel(img, "g"); b <- channel(img, "b")
   rb <- r*(r/(r+b) ) + b*(b/(r+b) )

   data <- array(NA, dim=dim(img))
   for ( i in 1:length(mean.idx))
   {
    filter <- (g[,,i]-r[,,i]+0.4)*(1-delta) + (g[,,i]-rb[,,i]+0.4)*delta
    mean.f <- mean(filter, na.rm=T)
    summary.f <- c(summary.f, mean.f)
    t <- fit.day1(mean.f, size)
    if( t < 0 ) t <- 0
    dist <- try( distmap(filter, t=t) )
    if( length(dist)==1)
    {
     writeImage(tile(img, nx=3), file.path(out.dir, paste("img", k, ".jpg", sep="")) )
     writeImage(tile( Image(array( rep(idx,3), dim=dim(img))), nx=3), file.path(out.dir, paste("idx", k, ".jpg", sep="")) )
     summary.size <- c(summary.size, size)
     next
    }
    widx <-  watershed( dist, tolerance=1, ext=3 )
    data[,,i] <- widx@.Data
   }
   widx@.Data <- data
   ft <- hullFeatures ( widx )

   ###remove noisy objects
   ifelse (size <= 20000, noise.cut <- 30, noise.cut <- 60)
   idx <- rmObjects(widx,  lapply(ft, function(x) which( x[,"h.s"] < noise.cut
                                                       | x[,"h.p"] < noise.cut
                                                       | x[,"h.s"]/x[,"h.p"] < 1.5)))

   if ( !is.na(which.label) ) idx[array(label, dim(idx))] <- 0

   idx[ img==0] <- 0

   ft <- hullFeatures(idx)
   tmp.size <-  unlist( lapply(ft, function(x) sum(x[,"h.s"]) ) )
   summary.size <- c(summary.size, tmp.size)

   writeImage(tile(img, nx=3), file.path(out.dir, paste("img", k, ".jpg", sep="")) )
   writeImage(tile(idx, nx=3), file.path(out.dir, paste("idx", k, ".jpg", sep="")) )

   cat (m, "\t", n, "\t", k, "\n")

  } ###close of day


  img <- readImage( file.path(out.dir, paste("img", 1:k, ".jpg", sep="")), TrueColor )
  idx <- readImage( file.path(out.dir, paste("idx", 1:k, ".jpg", sep="")) )
  writeImage( tile(img, nx=6), file.path(html.dir, paste(plant[n], ".img.jpg", sep="")))
  writeImage( tile(idx, nx=6), file.path(html.dir, paste(plant[n], ".idx.jpg", sep="")))
  file <- file.path(out.dir, paste( "img", 1:k, ".jpg", sep="") )
  file.remove(file)
  file <- file.path(out.dir, paste( "idx", 1:k, ".jpg", sep="") )
  file.remove(file)

 } ###close of plant





#############################################################################################################################
# image analysis for daytime pictures #############################################################################################################################



 library(EBImage)



 all.tray <- c("cam5", "cam2",
               "cam15", "cam18", "cam4", "cam8", "cam28", "cam21", "cam30", "cam24", "cam13", "cam22", "cam11", "cam16", "cam25", "cam23", "cam26", "cam19",
               "Tray 1R2", "Tray 2R2",
               "Tray 1L2", "Tray 1L3", "Tray 1L6", "Tray 1L7", "Tray 1R6", "Tray 1R7", "Tray 1R10", "Tray 1R11", "Tray 2L2", "Tray 2L3", "Tray 2L6", "Tray 2L7", "Tray 2R6", "Tray 2R7", "Tray 2R10", "Tray 2R11")

 day.cut <- matrix(scan("/home/xuzhang/image2/daycut.txt", what=1,comment.char="#", nlines=length(all.tray)), byrow=T, nc=3) ###the mean light intensity thresholds to distinguish day and night pictures
 extra.day.cut <- matrix(scan("/home/xuzhang/image2/daycut.txt", what=1, skip=length(all.tray)), byrow=T, nc=3) ###some unusuall tray, mean light intensity thresholds to disguish day and night pictures

 labels <- matrix(scan( "/home/xuzhang/image2/labels.txt", what="a", sep="\t"), byrow=T, nc=2)

 fit.day <- function(x1, x2) { pred <- 0.12 + x1*0.475 - x2*0.00000130 } ###function for estimation of background threshold for noontime images



 m <- 1 ###select a flat

 ###general function for estimation of background threshold
 if(m %in% c(1:6) )       fit.day1 <- function(x1, x2) {  0.335 + x1*0.470 - x2*0.00000146 }  #for spain spring
 if(m %in% c(7:10) )      fit.day1 <- function(x1, x2) {  0.305 + x1*0.470 - x2*0.00000146 }  #for spain summer
 if(m %in% c(11:14) )     fit.day1 <- function(x1, x2) {  0.335 + x1*0.470 - x2*0.00000146 }  #for sweden spring
 if(m %in% c(15:18) )     fit.day1 <- function(x1, x2) {  0.305 + x1*0.470 - x2*0.00000146 }  #for sweden summer

 if(m %in% c(21:24) )     fit.day1 <- function(x1, x2) {  0.305 + x1*0.470 - x2*0.00000146 }  #for 2010 fall
 if(m %in% c(19, 25:28) ) fit.day1 <- function(x1, x2) {  0.325 + x1*0.470 - x2*0.00000146 }  #for 2010 winter
 if(m %in% c(29:32) )     fit.day1 <- function(x1, x2) {  0.305 + x1*0.470 - x2*0.00000146 }  #for 2040 fall
 if(m %in% c(20, 33:36) ) fit.day1 <- function(x1, x2) {  0.325 + x1*0.470 - x2*0.00000146 }  #for 2040 winter

 which.tray <- all.tray[m]


 dir.create( paste("/home/xuzhang/image2/view2/", which.tray, sep="") )
 dir.create( paste("/home/xuzhang/image2/saved/", which.tray, sep="") )

 out.dir <- tempdir()
 html.dir <- paste("/home/xuzhang/image2/view2/", which.tray, "/", sep="")
 crop.dir <- paste("/home/xuzhang/image2/crop/", which.tray, "/", sep="")
 summary.dir <- paste("/home/xuzhang/image2/saved/", which.tray, "/", sep="")

 layout <- scan( paste("/home/xuzhang/image2/tray.layout/", which.tray, ".txt", sep=""), what="a", sep="\t" )
 plant <- layout[ length(layout):1 ] ###the order is reversed, facing barcode or not

 if (m %in% c(1:18) ) tray.dir <- paste("/home/borevitzlab/g2data/albums/Growth Chambers_001/Growth Chambers/Cams/", which.tray, sep="")
 if (m %in% c(19, 21:28) ) tray.dir <- paste("/home/borevitzlab/g2data_borevitz_chambers/albums/BSLC Chambers/Chamber 1/", which.tray, sep="")
 if (m %in% c(20, 29:36) ) tray.dir <- paste("/home/borevitzlab/g2data_borevitz_chambers/albums/BSLC Chambers/Chamber 2/", which.tray, sep="")

 coords <- matrix( scan( paste("/home/xuzhang/image2/matchCoord.", which.tray, ".txt", sep=""), what="a", sep="\t") , byrow=T, nc=3)
 day.dir <- sub(tray.dir, "", coords[, 1])
 day.dir <- matrix(unlist(strsplit(day.dir, "/")), byrow=T, nc=3)[,2]
 day.dir <- names(table(day.dir))

 for (n in 1:length(plant))
 {

  plant.summary <- time <- c()

  for (k in 1:length(day.dir))
  {
   which.day <-  day.dir[k]

   filename <-  matrix( scan( paste("/home/xuzhang/image2/camera.time/", which.tray, "/", which.day, ".filename", sep=""), what="a"), byrow=T, nc=4)[,4]
   time.lap <-  matrix( scan( paste("/home/xuzhang/image2/camera.time/", which.tray, "/", which.day, ".timelap", sep=""), what="a"), byrow=T, nc=5)[,4:5]
   time.lap <-  paste( gsub(":", "-", time.lap[,1], fixed=T), time.lap[,2] )
   time.lap <-   as.numeric( as.POSIXct( strptime(time.lap, format="%Y-%m-%d %H:%M:%S") ) )
   time.dir <- paste(tray.dir, which.day, filename, sep="/")

   which.coord <- coords[ grep(which.day, coords[,1]), ]
   time.lap <- time.lap[ match (which.coord [,1], time.dir)]
   time.dir <- time.dir[ match (which.coord [,1], time.dir)]
   time.order <- c(1:length(time.dir))
   time.order <- time.order[ which( !is.na( which.coord[,3]) ) ]
   time.lap <- time.lap[ which( !is.na( which.coord[,3]) ) ]

   ###read in image stack and trim images to the same size
   img <- file.path(crop.dir, paste(plant[n], "_day", k, "_time", time.order, ".jpg", sep="") )
   if (k==1)   {tmp.img <- readImage(img[1], TrueColor); img.dim <- dim(tmp.img); size <- 1000  }
   data <- array(0, c(img.dim[1:2], length(img)) )
   for (i in 1:length(img))
   {
    tmp.img <- readImage(img[i], TrueColor)
    min.r <- min( dim(tmp.img)[1], img.dim[1] )
    min.c <- min( dim(tmp.img)[2], img.dim[2] )
    tmp.data <- tmp.img@.Data[1:min.r, 1:min.c, 1]
    data[1:min.r,1:min.c,i] <- tmp.data
   }
   img <- Image( data, dim=c(img.dim[1:2], length(img)), TrueColor )

   ###remove nighttime images
   mean.int <- apply( channel(img, "g")-channel(img, "r"), 3, mean)
   ifelse(k < day.cut[m,3], mean.idx <- which(mean.int < day.cut[m,1]), mean.idx <- which(mean.int < day.cut[m,2]) )
   day.cut.idx <- which(extra.day.cut[,1]==m & extra.day.cut[,2]==n )
   if(length(day.cut.idx)>0) mean.idx <- which(mean.int < extra.day.cut[day.cut.idx, 3] )

   tmp.idx <- mean.idx[ which.max(mean.int[mean.idx]) ]
   tmp.img <- img[,, tmp.idx ]
   tmp.r <- channel(tmp.img, "r"); tmp.g <- channel(tmp.img, "g"); tmp.b <- channel(tmp.img, "b")
   tmp.rb <- tmp.r*(tmp.r/(tmp.r+tmp.b) ) + tmp.b*(tmp.b/(tmp.r+tmp.b) )

   delta <- 0.35* (50000-size)/50000
   if( delta < 0 ) delta <- 0
   filter <- (tmp.g-tmp.r)*(1-delta) + (tmp.g-tmp.rb)*delta
   mean.f <- mean(filter, na.rm=T)
   t <- fit.day(mean.f, size)
   if( t < 0 ) t <- 0
   dist <-  try( distmap(filter, t=t) )
   if(length(dist)==1)
   {
    time <- c(time, time.lap[mean.idx])
    plant.summary <- c(plant.summary, rep(size, length(mean.idx))  )
    next
   }

   widx <-  watershed( dist, tolerance=1, ext=3 )
   ft <- hullFeatures ( widx )
   idx <- rmObjects(widx,  list( which( ft[,"h.effr"]<=5 | ft[,"h.sf"]>5 ) ) )

   ###remove green labels and sticks
   which.label <- labels[ which( labels[,1] == paste(which.tray, plant[n], k, sep=".") ), 2]
   if ( !is.na(which.label) )
   {
    load ( paste("/home/xuzhang/image2/labels/", which.tray, "/", which.label, ".RData", sep="") )
    idx[label] <- 0
   }

   idx[tmp.img==0] <- 0

   ft <- hullFeatures(idx)
   size <-  sum(ft[,"h.s"])  ###rosette size at noontime

   delta <- 0.35* (50000-size)/50000
   if( delta < 0 ) delta <- 0

   img <- img[,,mean.idx]
   time.lap <- time.lap[mean.idx]

   data <- array(NA, dim=dim(img) )
   for (i in 1:dim(img)[3])
   {
    tmp.img <- img[,,i]
    tmp.r <- channel(tmp.img, "r"); tmp.g <- channel(tmp.img, "g"); tmp.b <- channel(tmp.img, "b")
    tmp.rb <- tmp.r*(tmp.r/(tmp.r+tmp.b) ) + tmp.b*(tmp.b/(tmp.r+tmp.b) )

    filter <- (tmp.g-tmp.r+0.4)*(1-delta) + (tmp.g-tmp.rb+0.4)*delta
    mean.f <- mean(filter, na.rm=T)
    t <- fit.day1(mean.f, size)
    if( t < 0 ) t <- 0
    dist <-  try( distmap(filter, t=t) )
    if(length(dist)==1)
    {
     data[,,i] <- idx@.Data
     next
    }
    widx <-  watershed( dist, tolerance=1, ext=3 )
    data[,,i] <- widx@.Data
   }
   widx@.Data <- data
   ft <- hullFeatures ( widx )

   ###remove noisy objects
   ifelse (size <= 20000, noise.cut <- 30, noise.cut <- 60)
   idx <- rmObjects(widx,  lapply(ft, function(x) which( x[,"h.s"] < noise.cut
                                                       | x[,"h.p"] < noise.cut
                                                       | x[,"h.s"]/x[,"h.p"] < 1.5)))

   ###remove green labels and sticks
   if ( !is.na(which.label) ) idx[array(label, dim(idx))] <- 0

   idx[ img==0] <- 0

   ft <- hullFeatures(idx)


   time <- c(time, time.lap)
   plant.summary <- c(plant.summary, unlist( lapply(ft, function(x) sum(x[,"h.s"]) ) )  )


   #writeImage( tile( idx, nx=12), file.path(widx.dir, paste(plant[n], "_day", k, ".jpg", sep="") ))
   #for (i in 1:dim(idx)[3]) writeImage(Image(idx[,,i]), file.path(widx.dir, paste(plant[n], "_day", k, "_time", i, ".jpg", sep="") ))

   cat(n, "\t", which.day, "\n")

  } ###close of day


  save( plant.summary, time, file=file.path(summary.dir, paste(plant[n], "_summaryday.RData") ) )


 } ###close of plant
