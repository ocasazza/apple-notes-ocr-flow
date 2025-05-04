#!/usr/bin/osascript

-- Apple Notes Export Script
-- This script exports Apple Notes content directly as text files
-- Usage: osascript export_notes.scpt <output_directory> [<notes_folder>]

on run argv
    -- Get the output directory from arguments
    set outputDir to item 1 of argv
    
    -- Check if a specific folder was specified
    set specificFolder to ""
    if (count of argv) > 1 then
        set specificFolder to item 2 of argv
    end if
    
    -- Make sure the output directory exists
    do shell script "mkdir -p " & quoted form of outputDir
    
    -- Create a directory for text files
    set textDir to outputDir & "/text"
    do shell script "mkdir -p " & quoted form of textDir
    
    tell application "Notes"
        -- Get the notes to process
        set notesToProcess to {}
        
        if specificFolder is "" then
            -- Get all notes from all folders
            set notesToProcess to every note
        else
            -- Get notes from the specified folder
            set folderFound to false
            
            repeat with f in folders
                if name of f is specificFolder then
                    set notesToProcess to every note in f
                    set folderFound to true
                    exit repeat
                end if
            end repeat
            
            if not folderFound then
                return "Error: Folder '" & specificFolder & "' not found."
            end if
        end if
        
        -- Process each note
        set noteCount to count of notesToProcess
        set successCount to 0
        
        -- Create a list to store text file paths
        set textPaths to {}
        
        repeat with i from 1 to noteCount
            set currentNote to item i of notesToProcess
            
            -- Get note name and sanitize it for use as a filename
            set noteName to name of currentNote
            set sanitizedName to my sanitizeFilename(noteName)
            
            -- If sanitized name is empty, use a generic name with the index
            if sanitizedName is "" then
                set sanitizedName to "note_" & i
            end if
            
            -- Create a unique filename with timestamp to avoid collisions
            set currentDate to current date
            set timeStamp to ((year of currentDate) & "-" & (month of currentDate as integer) & "-" & (day of currentDate) & "_" & (time of currentDate))
            set fileName to sanitizedName & "_" & timeStamp
            set textPath to textDir & "/" & fileName & ".txt"
            
            -- Get the note content
            set noteContent to body of currentNote
            
            -- Save the note content to a text file
            try
                do shell script "echo " & quoted form of noteContent & " > " & quoted form of textPath
                
                -- Add the text path to our list
                set end of textPaths to textPath
                
                set successCount to successCount + 1
            on error errMsg
                log "Error saving note '" & noteName & "': " & errMsg
            end try
        end repeat
        
        -- Save the list of text paths to a file
        set textPathsFile to outputDir & "/text_paths.txt"
        do shell script "touch " & quoted form of textPathsFile
        
        repeat with textPath in textPaths
            do shell script "echo " & quoted form of textPath & " >> " & quoted form of textPathsFile
        end repeat
        
        -- Return a summary
        return "Exported " & successCount & " of " & noteCount & " notes to text files in " & textDir
    end tell
end run

-- Function to sanitize a filename by removing invalid characters
on sanitizeFilename(filename)
    set invalidChars to {":", "/", "\\", "*", "?", "\"", "<", ">", "|"}
    set sanitized to filename
    
    repeat with c in invalidChars
        set sanitized to my replaceText(sanitized, c, "_")
    end repeat
    
    -- Trim leading/trailing whitespace
    set sanitized to my trim(sanitized)
    
    return sanitized
end sanitizeFilename

-- Function to replace text in a string
on replaceText(theText, searchString, replacementString)
    set AppleScript's text item delimiters to searchString
    set theTextItems to text items of theText
    set AppleScript's text item delimiters to replacementString
    set theText to theTextItems as text
    set AppleScript's text item delimiters to ""
    return theText
end replaceText

-- Function to trim whitespace from beginning and end of text
on trim(theText)
    -- Trim leading whitespace
    repeat while theText begins with " " or theText begins with tab
        set theText to text 2 thru end of theText
    end repeat
    
    -- Trim trailing whitespace
    repeat while theText ends with " " or theText ends with tab
        set theText to text 1 thru ((length of theText) - 1) of theText
    end repeat
    
    return theText
end trim
